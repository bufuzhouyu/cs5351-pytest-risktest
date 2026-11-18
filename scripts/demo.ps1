<#
.SYNOPSIS
    One-command live demo for the CS5351 presentation video.

.DESCRIPTION
    Copies a generated subject into a fresh temporary folder, records dependency
    traces, breaks one feature module, shows the selection plan, runs only the
    affected tests, and prints the machine-readable report. The repository itself
    is not modified.

.EXAMPLE
    .\scripts\demo.ps1
    .\scripts\demo.ps1 -NoPause
#>
param(
    [switch]$NoPause,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$srcPath = Join-Path $Root "src"

if (-not $Python) {
    $candidates = @()
    $found = Get-Command python -ErrorAction SilentlyContinue
    if ($found) { $candidates += $found.Source }
    $candidates += "D:\anaconda\python.exe"
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (-not (Test-Path $candidate)) { continue }
        & $candidate -c "import pytest, sys; assert sys.version_info >= (3, 12)" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $Python = $candidate; break }
    }
    if (-not $Python) { throw "No Python 3.12+ interpreter with pytest was found. Pass -Python <path>." }
}

$Stamp = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$Work = Join-Path $env:TEMP ("risktest-demo-" + $Stamp)
$Tests = Join-Path $Work "tests"
$Source = Join-Path $Root "benchmark\subjects\subject_01"
$WarmReport = Join-Path $Work ".risktest\warm.json"
$RunReport = Join-Path $Work ".risktest\run.json"
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Banner([string]$Text) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host ("  " + $Text) -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}

function Wait-Step([string]$Text) {
    Write-Host ""
    Write-Host (">> " + $Text) -ForegroundColor Yellow
    if (-not $NoPause) { [void](Read-Host "   Press Enter to continue") }
}

function Clear-Bytecode([string]$Directory) {
    Get-ChildItem -Path $Directory -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
        ForEach-Object { [System.IO.Directory]::Delete($_.FullName, $true) }
}

function Show-RunSummary([string]$ReportPath, [string]$Label) {
    if (-not (Test-Path $ReportPath)) { return }
    $report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    $skipped = [math]::Round([double]$report.skip_rate * 100)
    Write-Host ("   {0}: selected {1}/{2}, skipped {3}%, failures {4}" -f `
        $Label, $report.selected, $report.total_tests, $skipped, $report.failed) -ForegroundColor Green
}

Write-Banner "pytest-risktest  /  CS5351 software engineering project"
Write-Host ("Repository : " + $Root)
Write-Host ("Demo target: " + $Work + "  (generated project, 88 tests)")

New-Item -ItemType Directory -Force -Path $Work | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $Work -Recurse -Force
$CopiedState = Join-Path $Work ".risktest"
if ([System.IO.Directory]::Exists($CopiedState)) { [System.IO.Directory]::Delete($CopiedState, $true) }
Clear-Bytecode $Work
$env:PYTHONPATH = $srcPath + ";" + $Work
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Wait-Step "Step 1. Run every test once and record what each test executes"
& $Python -m pytest -q --no-header -p no:cacheprovider -p pytest_risktest.plugin `
    --rootdir=$Work --risktest --risktest-policy=off `
    --risktest-report=$WarmReport $Tests
Show-RunSummary $WarmReport "warm-up"

Wait-Step "Step 2. Break one feature module (simulated regression)"
$Feature = Join-Path $Work "app\features\feature_02.py"
$Original = Get-Content $Feature -Raw
$Broken = $Original -replace "WEIGHT = \d+", "WEIGHT = 1"
if ($Broken -eq $Original) { throw "The demo mutation did not apply." }
[System.IO.File]::WriteAllText($Feature, $Broken, $Utf8)
Clear-Bytecode $Work
Write-Host "   changed app/features/feature_02.py"

Wait-Step "Step 3. Inspect the selection plan before running anything"
& $Python -m pytest_risktest impact --root $Work --policy safe --limit 8 $Tests

Wait-Step "Step 4. Run only the affected tests, ordered by risk"
& $Python -m pytest -q --no-header -p no:cacheprovider -p pytest_risktest.plugin `
    --rootdir=$Work --risktest --risktest-policy=safe `
    --risktest-report=$RunReport $Tests
Show-RunSummary $RunReport "selective run"
Write-Host "   The run fails on purpose. The failure is reported, not hidden." -ForegroundColor Yellow

Wait-Step "Step 5. Restore the file and read the run report"
[System.IO.File]::WriteAllText($Feature, $Original, $Utf8)
Clear-Bytecode $Work
& $Python -m pytest_risktest report --report $RunReport --format markdown

Write-Banner "Demo complete"
Write-Host ("Reports: " + (Join-Path $Work ".risktest") + "\run.json, run.md, run.html")
Write-Host "For a real repository use the same commands from README.md"