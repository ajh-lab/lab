param(
  [string]$EnvPath = (Join-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) '.env'),
  [switch]$SkipToolboxCreate
)

$ErrorActionPreference = 'Stop'

if (!(Test-Path $EnvPath)) {
  throw "Env file not found: $EnvPath"
}

$envMap = @{}
Get-Content $EnvPath | ForEach-Object {
  if ($_ -match '^\s*#') { return }
  if ($_ -match '^([^=]+)=(.*)$') {
    $envMap[$matches[1].Trim()] = $matches[2]
  }
}

$wsHost = $envMap['AI_WORKSTATION_IP']
$user = $envMap['AI_WORKSTATION_USER']
if ([string]::IsNullOrWhiteSpace($wsHost) -or [string]::IsNullOrWhiteSpace($user)) {
  throw 'Missing AI_WORKSTATION_IP or AI_WORKSTATION_USER in .env'
}

$remote = @'
set -e
if [ ! -d /mnt/ai/llama/amd-strix-halo-toolboxes/.git ]; then
  git clone https://github.com/kyuz0/amd-strix-halo-toolboxes /mnt/ai/llama/amd-strix-halo-toolboxes
fi
cd /mnt/ai/llama/amd-strix-halo-toolboxes
git pull --ff-only
if [ "__SKIP_TOOLBOX__" = "0" ]; then
  toolbox list | grep -q 'llama-rocm-7.2.2' || toolbox create --assumeyes llama-rocm-7.2.2 --image docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.2.2 -- --device /dev/dri --device /dev/kfd --group-add video --group-add render --group-add sudo --security-opt seccomp=unconfined
  toolbox run -c llama-rocm-7.2.2 llama-cli --list-devices | sed -n '1,20p'
fi
echo "BACKEND_SYNC_OK"
'@

$skip = if ($SkipToolboxCreate) { '1' } else { '0' }
$remote = $remote.Replace('__SKIP_TOOLBOX__', $skip)

$remotePath = "/tmp/strix-backend-sync-$([guid]::NewGuid().ToString('N')).sh"
$localTemp = Join-Path $env:TEMP ([IO.Path]::GetFileName($remotePath))
Set-Content -Path $localTemp -Value $remote -NoNewline

scp -i "$HOME/.ssh/id_rsa" $localTemp "$user@$wsHost`:$remotePath" | Out-Null
ssh -i "$HOME/.ssh/id_rsa" "$user@$wsHost" "bash $remotePath; rm -f $remotePath"

Remove-Item -Force $localTemp -ErrorAction SilentlyContinue
