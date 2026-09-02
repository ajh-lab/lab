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

  $readyError = $null
  try {
    & $helper -Title 'Ready without decisions' -BodyPath $bodyPath -ExecutionTier Balanced -ReasoningEffort Medium -RepositoryPath $repoRoot -SkipGitHubLookup -AgentQueue Ready -WhatIf
  } catch {
    $readyError = $_.Exception.Message
  }
  if ($readyError -notmatch 'requires resolved dependencies') { throw 'Ready must fail closed without resolved dependencies.' }

  $duplicateError = $null
  try {
    $duplicateMock = { param([string[]]$Arguments) '[{"number":42,"title":"Existing","url":"https://example.invalid/issues/42"}]' }
    & $helper -Title 'Duplicate' -BodyPath $bodyPath -ExecutionTier Balanced -ReasoningEffort Medium -RepositoryPath $repoRoot -GitHubInvoker $duplicateMock -Confirm:$false
  } catch {
    $duplicateError = $_.Exception.Message
  }
  if ($duplicateError -notmatch 'Likely duplicate') { throw 'Duplicate detection must fail before issue creation.' }

  $calls = [System.Collections.Generic.List[string]]::new()
  $mock = {
    param([string[]]$Arguments)
    $calls.Add(($Arguments -join ' '))
    if ($Arguments[0..1] -join ' ' -eq 'issue create') { return 'https://github.com/ajh-lab/lab/issues/999' }
    if ($Arguments[0..1] -join ' ' -eq 'project view') { return '{"id":"project-id"}' }
    if ($Arguments[0..1] -join ' ' -eq 'project field-list') { return '{"fields":[{"id":"priority-field","name":"Priority","options":[{"id":"priority-option","name":"Medium"}]},{"id":"area-field","name":"Area","options":[{"id":"area-option","name":"Platform"}]},{"id":"target-field","name":"Target","options":[{"id":"target-option","name":"Next"}]},{"id":"type-field","name":"Work Type","options":[{"id":"type-option","name":"Feature"}]},{"id":"tier-field","name":"Execution Tier","options":[{"id":"tier-option","name":"Balanced"}]},{"id":"effort-field","name":"Reasoning Effort","options":[{"id":"effort-option","name":"Medium"}]},{"id":"queue-field","name":"Agent Queue","options":[{"id":"queue-option","name":"Backlog"}]}]}' }
    if ($Arguments[0..1] -join ' ' -eq 'project item-add') { return '{"id":"item-id"}' }
    return '{"data":{"updateProjectV2ItemFieldValue":{"projectV2Item":{"id":"item-id"}}}}'
  }
  $result = & $helper -Title 'Mocked write boundary' -BodyPath $bodyPath -ExecutionTier Balanced -ReasoningEffort Medium -RepositoryPath $repoRoot -SkipGitHubLookup -GitHubInvoker $mock -Confirm:$false | ConvertFrom-Json
  if ($result.issue_number -ne 999 -or $result.dispatches_worker) { throw 'Mocked write result is invalid.' }
  if ($calls.Count -ne 11) { throw 'Expected issue creation, Project reads, item creation, and seven field writes.' }
  Write-Host 'PASS: New-DroneOpsIssue WhatIf plan'
} finally {
  Remove-Item -LiteralPath $bodyPath -Force -ErrorAction SilentlyContinue
}
