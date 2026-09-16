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
. (Join-Path $PSScriptRoot "port.ps1")
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
Write-Host 'Waiting for the gateway to start...'
$Ready = $false
for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
  try { Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 | Out-Null; $Ready = $true; break } catch { Start-Sleep -Seconds 2 }
}
if (-not $Ready) { throw 'Gateway is not ready. Inspect docker compose logs gateway, then retry.' }
Start-Process $Url
Write-Host 'Stop all services with: docker compose stop'
$ConfiguredPassword = $env:BENCH_PASSWORD
if (-not $ConfiguredPassword) {
  $PasswordLine = Get-Content .env | Where-Object { $_ -like 'BENCH_PASSWORD=*' } | Select-Object -Last 1
  $ConfiguredPassword = $PasswordLine.Substring('BENCH_PASSWORD='.Length)
}
Write-Host "`nIgnition Designer connection"
Write-Host "Gateway: http://localhost:$Port"
Write-Host 'Username: benchmark'
Write-Host "Password: $ConfiguredPassword"
Write-Host 'Project: performance-lab'
Write-Host 'These are the initial-setup credentials stored in this lab configuration.'
Write-Host 'An existing gateway volume retains its original password; this launcher does not reset it.'
Write-Host 'Keep this terminal output private.'
