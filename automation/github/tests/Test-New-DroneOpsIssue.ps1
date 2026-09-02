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
  $cases = @(
    @{ path = $repoRoot; expected = 'ajh-lab/lab' },
    @{ path = 'C:\Users\adamj\SourceControl\lab\repositories\droneops-platform'; expected = 'ajh-lab/droneops-platform' },
    @{ path = 'C:\Users\adamj\SourceControl\lab\repositories\droneops-gateway'; expected = 'ajh-lab/droneops-gateway' }
  )
  foreach ($case in $cases) {
    $plan = & $helper -Title 'Representative dry-run' -BodyPath $bodyPath -ExecutionTier Balanced -ReasoningEffort Medium -RepositoryPath $case.path -SkipGitHubLookup -WhatIf
    $json = $plan | ConvertFrom-Json
    if ($json.repository -ne $case.expected) { throw "Repository derivation failed for $($case.expected)." }
    if ($json.dispatches_worker) { throw 'Dry run must not dispatch a worker.' }
    if ($json.writes.Count -ne 3) { throw 'Dry run plan is incomplete.' }
  }
  Write-Host 'PASS: New-DroneOpsIssue WhatIf plan'
} finally {
  Remove-Item -LiteralPath $bodyPath -Force -ErrorAction SilentlyContinue
}
