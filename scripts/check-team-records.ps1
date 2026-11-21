<#
.SYNOPSIS
    Show commit counts per author and warn about members without commits.

.EXAMPLE
    .\scripts\check-team-records.ps1 -Members "Zhang San","Li Si","Wang Wu"
#>
param(
    [string]$Repo = ".",
    [string[]]$Members = @()
)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path $Repo).Path
$git = "git"
if (Get-Command git -ErrorAction SilentlyContinue) { $git = (Get-Command git).Source }

function Invoke-Git([string[]]$Arguments) {
    & $git -C $Repo -c safe.directory=* @Arguments
}

$names = @(Invoke-Git @("log", "--format=%aN"))
$groups = @($names | Where-Object { $_ } | Group-Object | Sort-Object Count -Descending)

"Repository: $Repo"
"Commits scanned: " + (Invoke-Git @("rev-list", "--count", "HEAD"))
""
"Author                                      Commits"
"------------------------------------------- -------"
foreach ($group in $groups) {
    "{0,-43} {1,7}" -f $group.Name, $group.Count
}

"" 
"Author and email:"
Invoke-Git @("shortlog", "-sne", "HEAD")
""

if ($Members.Count -gt 0) {
    "Member check:"
    $missing = 0
    foreach ($member in $Members) {
        $match = $groups | Where-Object { $_.Name -like "*$member*" } | Select-Object -First 1
        if (-not $match) {
            $missing += 1
            "  MISSING  $member"
        }
        else {
            "  ok       {0}  ({1} commits)" -f $match.Name, $match.Count
        }
    }
    if ($missing -gt 0) {
        ""
        "Action: assign each missing member a real issue, branch and pull request."
        "Do not create empty commits on their behalf."
    }
}

""
"Latest commit per author:"
foreach ($group in $groups) {
    $last = (Invoke-Git @("log", "-1", "--author=$($group.Name)", "--format=%h %ad %s", "--date=short"))
    "  {0}: {1}" -f $group.Name, $last
}