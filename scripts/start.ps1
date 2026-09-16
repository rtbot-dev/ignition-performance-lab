param([string]$Benchmark = 'jython-vibration')
$ErrorActionPreference = 'Stop'
if ($Benchmark -notmatch '^[a-z0-9-]+$') { throw 'Invalid benchmark name' }
$Root = Split-Path $PSScriptRoot -Parent
$BenchPath = Join-Path $Root ('benchmarks/' + $Benchmark)
if (-not (Test-Path (Join-Path $BenchPath 'benchmark.json'))) { throw 'Unknown benchmark' }
Set-Location $BenchPath
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install and start Docker Desktop, then run this launcher again.' }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, then run this launcher again.' }
if (-not (Test-Path .env)) {
  Write-Host 'This starts a local Ignition trial and a bounded CPU load test.'
  Write-Host 'License: https://inductiveautomation.com/ignition/license'
  $consent = Read-Host 'Have you read and accepted the Ignition software license? [yes/no]'
  if ($consent -ne 'yes') { exit }
  $password = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
  [IO.File]::WriteAllText((Join-Path $BenchPath '.env'), "ACCEPT_IGNITION_EULA=Y`nBENCH_PASSWORD=$password`nBENCH_CPUS=3`n")
}
New-Item -ItemType Directory -Force results,runtime | Out-Null
if (-not (Test-Path runtime/plan.json)) { Copy-Item plan.json runtime/plan.json }
docker compose build prepare
if ($LASTEXITCODE -ne 0) { throw 'Benchmark image build failed.' }
docker compose up -d --no-build --remove-orphans
if ($LASTEXITCODE -ne 0) { throw 'Docker startup failed; inspect the output above.' }
Start-Process 'http://localhost:9088/data/perspective/client/performance-lab'
Write-Host 'Stop all services with: docker compose stop'
