[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)][string]$Title,
  [Parameter(Mandatory = $true)][string]$BodyPath,
  [ValidateSet('Economy', 'Balanced', 'Frontier')][string]$ExecutionTier,
  [ValidateSet('Low', 'Medium', 'High', 'Adaptive')][string]$ReasoningEffort,
  [string[]]$Labels = @('documentation'),
  [string]$Milestone,
  [ValidateSet('Critical', 'High', 'Medium', 'Low')][string]$Priority = 'Medium',
  [ValidateSet('Platform', 'Gateway', 'Field Infrastructure', 'Security', 'Future HQ')][string]$Area = 'Platform',
  [ValidateSet('Now', 'Next', 'Later')][string]$Target = 'Next',
  [ValidateSet('Bug', 'Feature', 'Architecture', 'Security', 'Documentation')][string]$WorkType = 'Feature',
  [ValidateSet('Backlog', 'Ready')][string]$AgentQueue = 'Backlog',
  [switch]$DependenciesResolved,
  [switch]$OwnerDecisionsResolved,
  [int]$ProjectNumber = 1,
  [string]$ProjectOwner = 'ajh-lab',
  [string]$RepositoryPath = (Get-Location).Path,
  [switch]$SkipGitHubLookup,
  [scriptblock]$GitHubInvoker
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
  if ($null -ne $GitHubInvoker) { return & $GitHubInvoker $Arguments }
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

function Get-ProjectField {
  param([object[]]$Fields, [string]$Name, [string]$Option)
  $field = @($Fields | Where-Object { $_.name -eq $Name })
  if ($field.Count -ne 1) { throw "Expected exactly one Project field named '$Name'." }
  $option = @($field[0].options | Where-Object { $_.name -eq $Option })
  if ($option.Count -ne 1) { throw "Expected exactly one '$Option' option for Project field '$Name'." }
  return [pscustomobject]@{ FieldId = $field[0].id; OptionId = $option[0].id }
}

function Set-ProjectItemField {
  param([string]$ProjectId, [string]$ItemId, [pscustomobject]$Field)
  $mutation = 'mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) { updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field, value: {singleSelectOptionId: $option}}) { projectV2Item { id } } }'
  [void](Invoke-BoundedGh -Arguments @('api', 'graphql', '-f', "query=$mutation", '-F', "project=$ProjectId", '-F', "item=$ItemId", '-F', "field=$($Field.FieldId)", '-F', "option=$($Field.OptionId)"))
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

if ($AgentQueue -eq 'Ready' -and (-not $DependenciesResolved -or -not $OwnerDecisionsResolved)) {
  throw 'Agent Queue=Ready requires resolved dependencies and owner decisions.'
}

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

if ($duplicates.Count -gt 0) { throw 'Likely duplicate open issue found; refusing to create a duplicate.' }
if (-not $PSCmdlet.ShouldProcess("$repository/$Title", 'Create issue and set Project metadata')) { return }

$createArgs = @('issue', 'create', '--repo', $repository, '--title', $Title, '--body-file', $BodyPath)
foreach ($label in $Labels) { $createArgs += @('--label', $label) }
if (-not [string]::IsNullOrWhiteSpace($Milestone)) { $createArgs += @('--milestone', $Milestone) }
$issueUrl = (Invoke-BoundedGh -Arguments $createArgs).Trim()
if ($issueUrl -notmatch '/issues/(\d+)$') { throw 'GitHub did not return an issue URL.' }
$issueNumber = $matches[1]

$project = (Invoke-BoundedGh -Arguments @('project', 'view', $ProjectNumber, '--owner', $ProjectOwner, '--format', 'json') | ConvertFrom-Json)
$fields = (Invoke-BoundedGh -Arguments @('project', 'field-list', $ProjectNumber, '--owner', $ProjectOwner, '--format', 'json') | ConvertFrom-Json).fields
$item = (Invoke-BoundedGh -Arguments @('project', 'item-add', $ProjectNumber, '--owner', $ProjectOwner, '--url', $issueUrl, '--format', 'json') | ConvertFrom-Json)

foreach ($entry in @(
    @{ name = 'Priority'; option = $Priority }, @{ name = 'Area'; option = $Area }, @{ name = 'Target'; option = $Target },
    @{ name = 'Work Type'; option = $WorkType }, @{ name = 'Execution Tier'; option = $ExecutionTier },
    @{ name = 'Reasoning Effort'; option = $ReasoningEffort }, @{ name = 'Agent Queue'; option = $AgentQueue }
  )) {
  Set-ProjectItemField -ProjectId $project.id -ItemId $item.id -Field (Get-ProjectField -Fields $fields -Name $entry.name -Option $entry.option)
}

[pscustomobject]@{ repository = $repository; issue_number = [int]$issueNumber; issue_url = $issueUrl; project_item_id = $item.id; dispatches_worker = $false } | ConvertTo-Json
