param([string]$Benchmark = 'jython-vibration')
& (Join-Path $PSScriptRoot 'scripts/start.ps1') -Benchmark $Benchmark
