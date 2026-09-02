[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)][string]$Title,
  [Parameter(Mandatory = $true)][string]$BodyPath,
  [ValidateSet('Economy', 'Balanced', 'Frontier')][string]$ExecutionTier,
  [ValidateSet('Low', 'Medium', 'High', 'Adaptive')][string]$ReasoningEffort,
  [string]$RepositoryPath = (Get-Location).Path,
  [switch]$SkipGitHubLookup
)

$ErrorActionPreference = 'Stop'

function Get-RepositorySlug {
  param([string]$Path)
  $remote = (& git -C $Path remote get-url origin).Trim()
  if ($remote -match 'github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$') {
    return "$($matches[1])/$($matches[2])"
  }
  throw 'origin must be a GitHub repository remote.'
}

function Test-AgentReadyIssueBody {
  param([string]$Body)
  $required = @('## Outcome', '## Scope', '## Ownership and Boundaries',
    '## Dependencies and Owner Decisions', '## Acceptance Criteria and Validation',
    '## Safety and Stop Boundaries', '## Execution Profile', '## Delivery Evidence')
  $missing = @($required | Where-Object { $Body -notmatch [regex]::Escape($_) })
  if ($missing.Count -gt 0) { throw "Issue body is missing required sections: $($missing -join ', ')" }
}

function Invoke-BoundedGh {
  param([string[]]$Arguments)
  $job = Start-Job -ArgumentList (, $Arguments) -ScriptBlock {
    param([string[]]$GhArguments)
    & gh @GhArguments
  }
  if (-not (Wait-Job $job -Timeout 30)) {
    Stop-Job $job
    Remove-Job $job
    throw 'GitHub CLI timed out after 30 seconds.'
  }
  $result = Receive-Job $job
  Remove-Job $job
  return $result
}

function Find-LikelyDuplicateIssues {
  param([string]$Repository, [string]$IssueTitle)
  $output = Invoke-BoundedGh -Arguments @('issue', 'list', '--repo', $Repository, '--state', 'open', '--search', $IssueTitle, '--json', 'number,title,url')
  if ([string]::IsNullOrWhiteSpace($output)) { return @() }
  return @($output | ConvertFrom-Json)
}

if (-not (Test-Path -LiteralPath $BodyPath)) { throw "Issue body not found: $BodyPath" }
$body = Get-Content -Raw -LiteralPath $BodyPath
Test-AgentReadyIssueBody -Body $body
$repository = Get-RepositorySlug -Path $RepositoryPath
$duplicates = if ($SkipGitHubLookup) { @() } else { Find-LikelyDuplicateIssues -Repository $repository -IssueTitle $Title }

$plan = [ordered]@{
  repository = $repository
  title = $Title
  execution_tier = $ExecutionTier
  reasoning_effort = $ReasoningEffort
  likely_duplicate_issues = @($duplicates | ForEach-Object { [ordered]@{ number = $_.number; title = $_.title; url = $_.url } })
  writes = @('create issue', 'add project item', 'set approved project fields')
  dispatches_worker = $false
}

if ($WhatIfPreference) {
  $plan | ConvertTo-Json -Depth 4
  return
}

throw 'Write mode is intentionally unavailable until Project field semantics are validated in issue #672. Use -WhatIf for no-write planning.'
