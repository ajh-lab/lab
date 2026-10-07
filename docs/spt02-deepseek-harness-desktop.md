# SPT02 DeepSeek Harness Desktop

Installed and checked on 2026-10-07 for the `helios` Windows account on
SPT02 (`192.168.1.86`, Windows hostname `DESKTOP-ID4I52L`).

## Start and use

In the SPT02 RDP session, open **DeepSeek Harness Desktop - Lab** from the
desktop or Start menu. This launcher supplies the existing LiteLLM credential
and the dedicated Desktop data directory. The installer-created plain
**DeepSeek Harness** shortcut does not supply this lab configuration.

- Application: official DeepSeek Harness Desktop `0.2.0-rc.2`, Windows x64.
- Provider: **AI Workstation LiteLLM** (`ai-workstation-litellm`).
- Default model: `qwen3.8-flash-next`.
- API endpoint: `http://192.168.1.123:4000/v1`.
- Advertised context: 262144; configured maximum output: 16384.
- Desktop backend binds loopback on an automatically selected port.
- Select the desired project folder in Desktop before starting project work.

The launcher sets `DSH_TELEMETRY_MODE=DISABLED` and injects
`LITELLM_API_KEY` into the process environment by decrypting the existing
user-bound DPAPI file. No separate DeepSeek cloud account or API key was
configured. The model requires the existing ai-workstation/LiteLLM service.

## Installation and state

- Application: `C:\Users\helios\AppData\Local\Programs\DeepSeek Harness`.
- Launcher: `C:\Users\helios\AppData\Local\DeepSeekHarnessDesktopInstall\Start-LabDesktop.ps1`.
- Data/config: `C:\Users\helios\.dsh-lab-desktop`.
- Provider patch: `.dsh-lab-desktop\cordis.patch.yml`.
- Desktop profile: `.dsh-lab-desktop\profiles\desktop`.
- Existing credential file: `C:\Users\helios\AppData\Local\DeepSeekHarness\litellm-key.dpapi`.
- Credential authority: OpenBao `secret/homelab/providers/litellm`, field
  `lan_api_key`; the installation reused the existing DPAPI materialization.
- Manual launch task: `DeepSeekHarness-Desktop-Manual`, interactive `helios`,
  limited privileges, no automatic trigger.

Desktop uses a separate home from the existing `.dsh-lab-iq4xs` web service.
Browser projects and history were copied into Desktop on 2026-10-07 as
described below. The web task `DeepSeekHarness-FlashNext` continues serving
port 3080. Its knowledge MCP configuration was not migrated.

## Browser project import

The import copied 15 session histories and 50 attachment files from browser
Harness `0.1.6-alpha.2`, retaining the original session IDs and project paths.
Desktop now has `wd_radar` (11 main chats and three subagent histories) and
`SPT` (one chat), alongside its existing `default-workspace` chat. The formerly
ungrouped `C:\SPT` conversation is registered under the `SPT` project.

Source data and destination data were backed up on SPT02 under:

```text
C:\Users\helios\AppData\Local\DeepSeekHarnessDesktopInstall\backups\browser-import-20261007-003412
```

`source` contains the hash-verified browser snapshot; `desktop-before` contains
the Desktop data before import. `source-manifest.json` records relative paths
and SHA-256 hashes. Import preserved existing Desktop history, merged the
workspace registry and copied attachments without replacing unequal files.
Both apps reported idle before Desktop was stopped for the import.

This is a one-time copy, not ongoing synchronization. Browser data, project
working directories, credentials, plugin packages and runtime configuration
were not modified. Continue imported work in Desktop; future browser and
Desktop conversations evolve independently. Desktop reads the historical V3
logs through its newer persistence implementation; do not copy newer Desktop
logs back into the older browser runtime.

Official installer:
<https://download.deepseek.com/desktop/dsh-latest-windows-x64.exe>.
The mutable download URL resolved to `0.2.0-rc.2` during installation.
SHA-256: `D61CD8882F8B8A1251144320493AD27920D15139503EBA2465B9579EEE720CFC`.
Authenticode status was `Valid`, signed by Hangzhou DeepSeek Artificial
Intelligence Co., Ltd.; silent installer exit code was 0.

## Verification and recovery

- Desktop processes and Host were running in the active `helios` RDP session.
- Authenticated Desktop HTTP returned 200.
- Authenticated provider API reported the declared LiteLLM provider; settings
  API confirmed that provider and `qwen3.8-flash-next` as the default.
- An authenticated direct LiteLLM completion returned `DESKTOP_READY`.
- Existing web authenticated HTTP remained 200.
- SPT.Server and EscapeFromTarkov retained their original process IDs.

These checks establish startup, configuration and a direct model response;
they are not a controlled model benchmark or a full interactive agent test.

If Desktop fails, inspect its application diagnostics and launcher logs under
`DeepSeekHarnessDesktopInstall`. Logs and credential files must not be copied
into issues or documentation without secret review. Fully quit Desktop before
changing its profile. For rollback, quit Desktop and use the existing web
launcher `C:\Users\helios\AppData\Local\DeepSeekHarness\Open-DeepSeekHarness.ps1`.
Keep Desktop data for recovery; uninstalling the app is not required to return
to the web service.
