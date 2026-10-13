/**
 * Open Brain MCP Server - Kubernetes Self-Hosted Version
 *
 * This is a modified version of the OB1 server that connects directly to
 * PostgreSQL + pgvector instead of Supabase. All MCP tools and the Hono
 * HTTP layer are preserved; only the data access layer is changed.
 *
 * Environment variables:
 *   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - PostgreSQL connection
 *   EMBEDDING_API_BASE - Base URL for OpenAI-compatible embedding API
 *   EMBEDDING_API_KEY - API key for the embedding service
 *   EMBEDDING_MODEL - Model name for embeddings (default: text-embedding-3-small)
 *   CHAT_API_BASE - Base URL for OpenAI-compatible chat API (defaults to EMBEDDING_API_BASE)
 *   CHAT_API_KEY - API key for chat service (defaults to EMBEDDING_API_KEY)
 *   CHAT_MODEL - Model name for metadata extraction (default: gpt-4o-mini)
 *   MCP_ACCESS_KEY - Authentication key for MCP endpoint (legacy; grants all scopes)
 *   MCP_KEYS_JSON - Optional JSON map of key -> { harness, scopes[], default_scope? };
 *                 "*" in scopes means all scopes.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPTransport } from "@hono/mcp";
import { Hono } from "hono";
import { z } from "zod";
import { Pool } from "postgres";
import { AsyncLocalStorage } from "node:async_hooks";

// --- Configuration ---

const DB_HOST = Deno.env.get("DB_HOST") || "127.0.0.1";
const DB_PORT = parseInt(Deno.env.get("DB_PORT") || "5432", 10);
const DB_NAME = Deno.env.get("DB_NAME") || "openbrain";
const DB_USER = Deno.env.get("DB_USER") || "postgres";
const DB_PASSWORD = Deno.env.get("DB_PASSWORD")!;

const EMBEDDING_API_BASE = Deno.env.get("EMBEDDING_API_BASE") || "https://openrouter.ai/api/v1";
const EMBEDDING_API_KEY = Deno.env.get("EMBEDDING_API_KEY") || Deno.env.get("OPENROUTER_API_KEY") || "";
const EMBEDDING_MODEL = Deno.env.get("EMBEDDING_MODEL") || "openai/text-embedding-3-small";

const CHAT_API_BASE = Deno.env.get("CHAT_API_BASE") || EMBEDDING_API_BASE;
const CHAT_API_KEY = Deno.env.get("CHAT_API_KEY") || EMBEDDING_API_KEY;
const CHAT_MODEL = Deno.env.get("CHAT_MODEL") || "openai/gpt-4o-mini";

const MCP_ACCESS_KEY = Deno.env.get("MCP_ACCESS_KEY") || "";

// --- Scope / harness-key auth model ---
// MCP_KEYS_JSON: JSON map of access key -> { harness, scopes[], default_scope? }.
// MCP_ACCESS_KEY (legacy) grants all scopes as "*".

interface CallerIdentity {
  harness: string;
  scopes: string[]; // ["*"] = all scopes
  defaultScope: string;
}

const KEY_MAP: Record<string, { harness: string; scopes: string[]; default_scope?: string }> =
  (() => {
    try {
      return JSON.parse(Deno.env.get("MCP_KEYS_JSON") || "{}");
    } catch {
      return {};
    }
  })();

const authStore = new AsyncLocalStorage<CallerIdentity>();

function currentCaller(): CallerIdentity {
  return authStore.getStore() || { harness: "unknown", scopes: ["*"], defaultScope: "global" };
}

function resolveScopes(requested?: string[]): string[] | null {
  const caller = currentCaller();
  const allowed = caller.scopes;
  if (!requested || !requested.length) {
    return allowed.includes("*") ? null : allowed; // null = no scope filter (all)
  }
  if (!allowed.includes("*")) {
    for (const s of requested) {
      if (!allowed.includes(s)) return null; // denied -> handled by caller
    }
  }
  return requested;
}

function scopeDenied(requested?: string[]): string | null {
  if (!requested || !requested.length) return null;
  const allowed = currentCaller().scopes;
  if (allowed.includes("*")) return null;
  const bad = requested.filter((s) => !allowed.includes(s));
  return bad.length ? `scope(s) not allowed for this key: ${bad.join(", ")}` : null;
}

function captureScope(requested?: string): string {
  const caller = currentCaller();
  const scope = requested || caller.defaultScope || "global";
  if (!caller.scopes.includes("*") && !caller.scopes.includes(scope)) {
    throw new Error(`scope not allowed for this key: ${scope}`);
  }
  return scope;
}

// --- PostgreSQL Connection Pool ---

const pool = new Pool({
  hostname: DB_HOST,
  port: DB_PORT,
  database: DB_NAME,
  user: DB_USER,
  password: DB_PASSWORD,
}, 20);

// --- Embedding & Metadata Extraction ---

async function getEmbedding(text: string): Promise<number[]> {
  const r = await fetch(`${EMBEDDING_API_BASE}/embeddings`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${EMBEDDING_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: text,
    }),
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => "");
    throw new Error(`Embedding API failed: ${r.status} ${msg}`);
  }
  const d = await r.json();
  return d.data[0].embedding;
}

async function extractMetadata(text: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${CHAT_API_BASE}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${CHAT_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: CHAT_MODEL,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Extract metadata from the user's captured thought. Return JSON with:
- "people": array of people mentioned (empty if none)
- "action_items": array of implied to-dos (empty if none)
- "dates_mentioned": array of dates YYYY-MM-DD (empty if none)
- "topics": array of 1-3 short topic tags (always at least one)
- "type": one of "observation", "task", "idea", "reference", "person_note"
Only extract what's explicitly there.`,
        },
        { role: "user", content: text },
      ],
    }),
  });
  const d = await r.json();
  try {
    return JSON.parse(d.choices[0].message.content);
  } catch {
    return { topics: ["uncategorized"], type: "observation" };
  }
}

// --- MCP Server Setup ---

const server = new McpServer({
  name: "open-brain",
  version: "1.0.0",
});

// Tool 1: Semantic Search (replaces supabase.rpc with raw SQL)
server.registerTool(
  "search_thoughts",
  {
    title: "Search Thoughts",
    description:
      "Search captured thoughts by meaning. Use this when the user asks about a topic, person, or idea they've previously captured.",
    inputSchema: {
      query: z.string().describe("What to search for"),
      limit: z.number().optional().default(10),
      threshold: z.number().optional().default(0.5),
      scopes: z.array(z.string()).optional().describe("Restrict search to these scopes (e.g. [\"lab\", \"global\"])"),
    },
  },
  async ({ query, limit, threshold, scopes }) => {
    const denied = scopeDenied(scopes);
    if (denied) return { content: [{ type: "text" as const, text: `Denied: ${denied}` }], isError: true };
    try {
      const qEmb = await getEmbedding(query);
      const embStr = `[${qEmb.join(",")}]`;
      const scopeFilter = resolveScopes(scopes);

      const client = await pool.connect();
      try {
        const result = await client.queryObject<{
          content: string;
          metadata: Record<string, unknown>;
          scope: string;
          similarity: number;
          created_at: string;
        }>(
          `SELECT content, metadata, scope, created_at,
                  1 - (embedding <=> $1::vector) AS similarity
           FROM thoughts
           WHERE 1 - (embedding <=> $1::vector) >= $2
             AND ($3::text[] IS NULL OR scope = ANY($3))
           ORDER BY embedding <=> $1::vector
           LIMIT $4`,
          [embStr, threshold, scopeFilter, limit]
        );

        if (!result.rows.length) {
          return {
            content: [{ type: "text" as const, text: `No thoughts found matching "${query}".` }],
          };
        }

        const results = result.rows.map((t, i) => {
          const m = t.metadata || {};
          const parts = [
            `--- Result ${i + 1} (${(t.similarity * 100).toFixed(1)}% match) ---`,
            `Scope: ${t.scope} | Provenance: ${m.provenance || "captured"} | Harness: ${m.harness || "unknown"}`,
            `Captured: ${new Date(t.created_at).toLocaleDateString()}`,
            `Type: ${m.type || "unknown"}`,
          ];
          if (Array.isArray(m.topics) && m.topics.length)
            parts.push(`Topics: ${(m.topics as string[]).join(", ")}`);
          if (Array.isArray(m.people) && m.people.length)
            parts.push(`People: ${(m.people as string[]).join(", ")}`);
          if (Array.isArray(m.action_items) && m.action_items.length)
            parts.push(`Actions: ${(m.action_items as string[]).join("; ")}`);
          parts.push(`\n${t.content}`);
          return parts.join("\n");
        });

        return {
          content: [
            {
              type: "text" as const,
              text: `Found ${result.rows.length} thought(s):\n\n${results.join("\n\n")}`,
            },
          ],
        };
      } finally {
        client.release();
      }
    } catch (err: unknown) {
      return {
        content: [{ type: "text" as const, text: `Error: ${(err as Error).message}` }],
        isError: true,
      };
    }
  }
);

// Tool 2: List Recent (replaces supabase query builder with raw SQL)
server.registerTool(
  "list_thoughts",
  {
    title: "List Recent Thoughts",
    description:
      "List recently captured thoughts with optional filters by type, topic, person, or time range.",
    inputSchema: {
      limit: z.number().optional().default(10),
      type: z.string().optional().describe("Filter by type: observation, task, idea, reference, person_note"),
      topic: z.string().optional().describe("Filter by topic tag"),
      person: z.string().optional().describe("Filter by person mentioned"),
      days: z.number().optional().describe("Only thoughts from the last N days"),
      scopes: z.array(z.string()).optional().describe("Restrict to these scopes"),
    },
  },
  async ({ limit, type, topic, person, days, scopes }) => {
    const denied = scopeDenied(scopes);
    if (denied) return { content: [{ type: "text" as const, text: `Denied: ${denied}` }], isError: true };
    try {
      const conditions: string[] = [];
      const params: unknown[] = [];
      let paramIdx = 1;

      const scopeFilter = resolveScopes(scopes);
      if (scopeFilter) {
        conditions.push(`scope = ANY($${paramIdx})`);
        params.push(scopeFilter);
        paramIdx++;
      }

      if (type) {
        conditions.push(`metadata->>'type' = $${paramIdx}`);
        params.push(type);
        paramIdx++;
      }
      if (topic) {
        conditions.push(`metadata->'topics' ? $${paramIdx}`);
        params.push(topic);
        paramIdx++;
      }
      if (person) {
        conditions.push(`metadata->'people' ? $${paramIdx}`);
        params.push(person);
        paramIdx++;
      }
      if (days) {
        conditions.push(`created_at >= NOW() - INTERVAL '${days} days'`);
      }

      const whereClause = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";

      const client = await pool.connect();
      try {
        const result = await client.queryObject<{
          content: string;
          metadata: Record<string, unknown>;
          created_at: string;
        }>(
          `SELECT content, metadata, created_at
           FROM thoughts
           ${whereClause}
           ORDER BY created_at DESC
           LIMIT $${paramIdx}`,
          [...params, limit]
        );

        if (!result.rows.length) {
          return { content: [{ type: "text" as const, text: "No thoughts found." }] };
        }

        const results = result.rows.map((t, i) => {
          const m = t.metadata || {};
          const tags = Array.isArray(m.topics) ? (m.topics as string[]).join(", ") : "";
          return `${i + 1}. [${new Date(t.created_at).toLocaleDateString()}] (${m.type || "??"}${tags ? " - " + tags : ""})\n   ${t.content}`;
        });

        return {
          content: [
            {
              type: "text" as const,
              text: `${result.rows.length} recent thought(s):\n\n${results.join("\n\n")}`,
            },
          ],
        };
      } finally {
        client.release();
      }
    } catch (err: unknown) {
      return {
        content: [{ type: "text" as const, text: `Error: ${(err as Error).message}` }],
        isError: true,
      };
    }
  }
);

// Tool 3: Stats (replaces supabase queries with raw SQL)
server.registerTool(
  "thought_stats",
  {
    title: "Thought Statistics",
    description: "Get a summary of all captured thoughts: totals, types, top topics, and people.",
    inputSchema: {},
  },
  async () => {
    const caller = currentCaller();
    const scopeParams: unknown[] = [];
    let scopeWhere = "";
    if (!caller.scopes.includes("*")) {
      scopeWhere = "WHERE scope = ANY($1)";
      scopeParams.push(caller.scopes);
    }
    try {
      const client = await pool.connect();
      try {
        const countResult = await client.queryObject<{ count: number }>(
          `SELECT COUNT(*)::int AS count FROM thoughts ${scopeWhere}`,
          scopeParams
        );

        const dataResult = await client.queryObject<{
          metadata: Record<string, unknown>;
          created_at: string;
        }>(
          `SELECT metadata, created_at FROM thoughts ${scopeWhere} ORDER BY created_at DESC`,
          scopeParams
        );

        const count = countResult.rows[0]?.count || 0;
        const data = dataResult.rows;

        const types: Record<string, number> = {};
        const topics: Record<string, number> = {};
        const people: Record<string, number> = {};

        for (const r of data) {
          const m = r.metadata || {};
          if (m.type) types[m.type as string] = (types[m.type as string] || 0) + 1;
          if (Array.isArray(m.topics))
            for (const t of m.topics) topics[t as string] = (topics[t as string] || 0) + 1;
          if (Array.isArray(m.people))
            for (const p of m.people) people[p as string] = (people[p as string] || 0) + 1;
        }

        const sort = (o: Record<string, number>): [string, number][] =>
          Object.entries(o)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const lines: string[] = [
          `Total thoughts: ${count}`,
          `Date range: ${
            data.length
              ? new Date(data[data.length - 1].created_at).toLocaleDateString() +
                " -> " +
                new Date(data[0].created_at).toLocaleDateString()
              : "N/A"
          }`,
          "",
          "Types:",
          ...sort(types).map(([k, v]) => `  ${k}: ${v}`),
        ];

        if (Object.keys(topics).length) {
          lines.push("", "Top topics:");
          for (const [k, v] of sort(topics)) lines.push(`  ${k}: ${v}`);
        }

        if (Object.keys(people).length) {
          lines.push("", "People mentioned:");
          for (const [k, v] of sort(people)) lines.push(`  ${k}: ${v}`);
        }

        return { content: [{ type: "text" as const, text: lines.join("\n") }] };
      } finally {
        client.release();
      }
    } catch (err: unknown) {
      return {
        content: [{ type: "text" as const, text: `Error: ${(err as Error).message}` }],
        isError: true,
      };
    }
  }
);

// Tool 4: Capture Thought (replaces supabase insert with raw SQL)
server.registerTool(
  "capture_thought",
  {
    title: "Capture Thought",
    description:
      "Save a new thought to the Open Brain. Generates an embedding and extracts metadata automatically.",
    inputSchema: {
      content: z.string().describe("The thought to capture"),
      scope: z.string().optional().describe("Scope to capture into (must be allowed for this key); defaults to the key's default scope"),
      provenance: z.enum(["captured", "human"]).optional().default("captured").describe("Who authored this capture"),
    },
  },
  async ({ content, scope, provenance }) => {
    try {
      const targetScope = captureScope(scope);
      const caller = currentCaller();

      const [embedding, metadata] = await Promise.all([
        getEmbedding(content),
        extractMetadata(content),
      ]);

      const embStr = `[${embedding.join(",")}]`;
      const meta = { ...metadata, source: "mcp", provenance, harness: caller.harness };

      const client = await pool.connect();
      try {
        await client.queryObject(
          `INSERT INTO thoughts (content, embedding, metadata, scope)
           VALUES ($1, $2::vector, $3::jsonb, $4)`,
          [content, embStr, JSON.stringify(meta), targetScope]
        );
      } finally {
        client.release();
      }

      let confirmation = `Captured as ${meta.type || "thought"} in scope ${targetScope}`;
      if (Array.isArray(meta.topics) && meta.topics.length)
        confirmation += ` -- ${(meta.topics as string[]).join(", ")}`;
      if (Array.isArray(meta.people) && meta.people.length)
        confirmation += ` | People: ${(meta.people as string[]).join(", ")}`;
      if (Array.isArray(meta.action_items) && meta.action_items.length)
        confirmation += ` | Actions: ${(meta.action_items as string[]).join("; ")}`;

      return {
        content: [{ type: "text" as const, text: confirmation }],
      };
    } catch (err: unknown) {
      return {
        content: [{ type: "text" as const, text: `Error: ${(err as Error).message}` }],
        isError: true,
      };
    }
  }
);

// --- Hono App with Auth Check ---

const app = new Hono();

app.all("*", async (c) => {
  const provided = c.req.header("x-brain-key") || new URL(c.req.url).searchParams.get("key");
  if (!provided) {
    return c.json({ error: "Missing access key" }, 401);
  }
  let identity: CallerIdentity;
  if (KEY_MAP[provided]) {
    const entry = KEY_MAP[provided];
    identity = {
      harness: entry.harness,
      scopes: entry.scopes?.length ? entry.scopes : ["*"],
      defaultScope: entry.default_scope || entry.scopes?.[0] || "global",
    };
  } else if (MCP_ACCESS_KEY && provided === MCP_ACCESS_KEY) {
    identity = { harness: "legacy", scopes: ["*"], defaultScope: "global" };
  } else {
    return c.json({ error: "Invalid or missing access key" }, 401);
  }

  return authStore.run(identity, async () => {
    const transport = new StreamableHTTPTransport();
    await server.connect(transport);
    return transport.handleRequest(c);
  });
});

Deno.serve({ port: parseInt(Deno.env.get("PORT") || "8000", 10) }, app.fetch);
