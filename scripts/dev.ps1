<#
.SYNOPSIS
    Developer entry point for the pytest-risktest project.

.EXAMPLE
    .\scripts\dev.ps1
    .\scripts\dev.ps1 -Benchmark
    .\scripts\dev.ps1 -Fast
#>
param(
    [switch]$Fast,
    [switch]$Benchmark,
    [switch]$Experiments,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "src"

function Invoke-Python {
    param([string[]]$Arguments)
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @Arguments
    }
    else {
        & "D:\anaconda\python.exe" @Arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "python $($Arguments -join ' ') failed" }
}

Push-Location $Root
try {
    if ($Clean) {
        Invoke-Python @("-m", "pytest_risktest", "clean", "--yes")
    }
    if ($Fast) {
        Invoke-Python @("-m", "pytest", "tests", "-q", "--no-header",
            "--ignore=tests/test_plugin_integration.py", "--ignore=tests/test_cli.py")
    }
    else {
        Invoke-Python @("-m", "pytest", "tests", "-q", "--no-header")
    }
    Invoke-Python @("scripts/make_burndown.py")
    if ($Experiments) {
        Invoke-Python @("benchmark/experiments/tracing_strategies.py")
        Invoke-Python @("benchmark/experiments/untraced_paths.py")
    }
    if ($Benchmark) {
        Invoke-Python @("benchmark/run_bench.py", "--subjects", "3", "--mutations", "3")
    }
}
finally {
    Pop-Location
}

