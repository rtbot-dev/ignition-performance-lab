# Dot-sourced by start.ps1. A user's explicit selection authorizes a Docker stop.
$Port = if ($env:LAB_PORT) { $env:LAB_PORT } elseif (Test-Path runtime/port) { (Get-Content runtime/port -Raw).Trim() } else { '9088' }
while ($true) {
  if ($Port -notmatch '^\d{4,5}$' -or [int]$Port -lt 1024 -or [int]$Port -gt 65535) {
    $Port = Read-Host 'Enter a port from 1024 to 65535 [9089]'
    if (-not $Port) { $Port = '9089' }; continue
  }
  $Owners = @(docker ps --filter "publish=$Port" --format '{{.Names}} {{.Label "com.docker.compose.project"}}')
  if ($LASTEXITCODE -ne 0) { throw 'Could not inspect Docker port allocations.' }
  $Conflicts = @($Owners | Where-Object { $_ -and (($_ -split ' ')[-1] -ne 'katenaria-lab-jython-vibration') } | ForEach-Object { ($_ -split ' ')[0] })
  $Occupied = $false
  if ($Owners.Count -eq 0) {
    $Occupied = @([System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() | Where-Object { $_.Port -eq [int]$Port }).Count -gt 0
  }
  if ($Conflicts.Count -eq 0 -and -not $Occupied) { break }
  if ($Conflicts.Count -gt 0) {
    Write-Host "Port $Port is used by Docker containers: $($Conflicts -join ', ')"
    Write-Host '1) Stop the listed containers (interrupts their services) and use this port'
  } else { Write-Host "Port $Port belongs to a local process. This launcher will not terminate it." }
  Write-Host '2) Use another port'
  Write-Host '3) Cancel'
  $Choice = Read-Host 'Choose [3]'
  switch ($Choice) {
    '1' {
      if ($Conflicts.Count -eq 0) { Write-Host 'Choose another port or stop the process yourself.'; break }
      foreach ($Container in $Conflicts) {
        docker stop $Container
        if ($LASTEXITCODE -ne 0) { throw "Could not stop $Container" }
      }
    }
    '2' { $Port = Read-Host 'New port [9089]'; if (-not $Port) { $Port = '9089' } }
    { $_ -eq '' -or $_ -eq '3' } { throw 'Cancelled. No additional changes made.' }
    default { Write-Host 'Choose 1, 2 or 3.' }
  }
}
$env:LAB_PORT = $Port
New-Item -ItemType Directory -Force runtime | Out-Null
Set-Content -Path runtime/port -Value $Port -Encoding ASCII
$Url = "http://localhost:$Port/data/perspective/client/performance-lab"
