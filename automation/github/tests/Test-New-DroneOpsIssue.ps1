$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$helper = Join-Path $repoRoot 'automation\github\New-DroneOpsIssue.ps1'
$bodyPath = Join-Path $env:TEMP 'droneops-issue-helper-test.md'

@'
## Outcome
Test outcome.
## Scope
Test scope.
## Ownership and Boundaries
Test boundaries.
## Dependencies and Owner Decisions
None.
## Acceptance Criteria and Validation
- [ ] Test.
## Safety and Stop Boundaries
No writes.
## Execution Profile
Balanced.
## Delivery Evidence
Dry run.
'@ | Set-Content -NoNewline -LiteralPath $bodyPath

try {
  $plan = & $helper -Title 'Representative dry-run' -BodyPath $bodyPath -ExecutionTier Balanced -ReasoningEffort Medium -RepositoryPath $repoRoot -SkipGitHubLookup -WhatIf
  $json = $plan | ConvertFrom-Json
  if ($json.repository -ne 'ajh-lab/lab') { throw 'Repository derivation failed.' }
  if ($json.dispatches_worker) { throw 'Dry run must not dispatch a worker.' }
  if ($json.writes.Count -ne 3) { throw 'Dry run plan is incomplete.' }
  Write-Host 'PASS: New-DroneOpsIssue WhatIf plan'
} finally {
  Remove-Item -LiteralPath $bodyPath -Force -ErrorAction SilentlyContinue
}
