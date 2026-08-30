param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "update", "doctor", "uninstall", "help")]
    [string]$Action = "install",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AgentKitArgs
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ToolkitRepo = if ($env:AGENT_KIT_REPO) { $env:AGENT_KIT_REPO } else { "udhawan97/agent-toolkit" }
$ToolkitRepoUrl = if ($env:AGENT_KIT_REPO_URL) { $env:AGENT_KIT_REPO_URL } else { "https://github.com/$ToolkitRepo.git" }
$ToolkitChannel = if ($env:AGENT_KIT_CHANNEL) { $env:AGENT_KIT_CHANNEL } else { "stable" }
$DefaultDataRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME ".agent-toolkit-source" }
$ToolkitSourceDir = if ($env:AGENT_KIT_SOURCE_DIR) { $env:AGENT_KIT_SOURCE_DIR } else { Join-Path $DefaultDataRoot "AgentToolkit" }
$ToolkitLegacyRoot = if ($env:AGENT_KIT_LEGACY_ROOT) { $env:AGENT_KIT_LEGACY_ROOT } else { "0ef3ac2ab866ac157e94d43b3104d8797489bd7f" }
$ActionWasExplicit = $PSBoundParameters.ContainsKey("Action")

function Show-Usage {
    @"
Agent Toolkit setup

Usage:
  .\setup.ps1 [install|update|doctor|uninstall] [agent-kit options]

Examples:
  .\setup.ps1
  .\setup.ps1 install --clients both --profile recommended
  .\setup.ps1 update
  .\setup.ps1 doctor --native
  .\setup.ps1 uninstall --remove-guidance

Environment:
  AGENT_KIT_AUTO_PREREQS  1 (default) installs missing Git/Python with winget; 0 disables
"@
}

function Refresh-ProcessPath {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $CurrentPath = $env:Path
    $PathParts = @($MachinePath, $UserPath, $CurrentPath) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    $env:Path = $PathParts -join [IO.Path]::PathSeparator
}

function Get-SupportedPython {
    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        & $Py.Source -3 -c "import sys, ensurepip, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{ Executable = $Py.Source; Prefix = @("-3") }
        }
    }
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) {
        & $Python.Source -c "import sys, ensurepip, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{ Executable = $Python.Source; Prefix = @() }
        }
    }
    return $null
}

function Install-Prerequisite([string]$Id, [string]$Label) {
    if ($env:AGENT_KIT_AUTO_PREREQS -eq "0") {
        throw "$Label is required; automatic prerequisite setup is disabled."
    }
    $Winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $Winget) {
        throw "$Label is required and winget is unavailable. Install $Label, then rerun this same command."
    }
    Write-Host "Agent Toolkit setup: installing missing prerequisite: $Label"
    & $Winget.Source install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install $Label. Install it manually, then rerun this same command."
    }
    Refresh-ProcessPath
}

if ($Action -eq "help") {
    Show-Usage
    return
}

if ($ToolkitChannel -notin @("stable", "main")) {
    throw "AGENT_KIT_CHANNEL must be stable or main."
}
if ([string]::IsNullOrWhiteSpace($ToolkitSourceDir) -or $ToolkitSourceDir -eq [System.IO.Path]::GetPathRoot($ToolkitSourceDir) -or $ToolkitSourceDir -eq $HOME) {
    throw "Refusing unsafe AGENT_KIT_SOURCE_DIR: $ToolkitSourceDir"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Install-Prerequisite "Git.Git" "Git"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $GitCandidate = Join-Path $env:ProgramFiles "Git\cmd"
    if (Test-Path (Join-Path $GitCandidate "git.exe") -PathType Leaf) {
        $env:Path = "$GitCandidate$([IO.Path]::PathSeparator)$env:Path"
    }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git was installed but is not available in this terminal. Open a new PowerShell window and rerun the same command."
}

$PythonSpec = Get-SupportedPython
if (-not $PythonSpec) {
    Install-Prerequisite "Python.Python.3.12" "Python 3.12"
    $PythonSpec = Get-SupportedPython
}
if (-not $PythonSpec) {
    throw "Python was installed but is not available in this terminal. Open a new PowerShell window and rerun the same command."
}
$PythonExecutable = $PythonSpec.Executable
$PythonPrefix = @($PythonSpec.Prefix)

$GitDir = Join-Path $ToolkitSourceDir ".git"
if (Test-Path $GitDir -PathType Container) {
    $Origin = (& git -C $ToolkitSourceDir remote get-url origin).Trim()
    $AllowedOrigins = @(
        $ToolkitRepoUrl,
        "https://github.com/$ToolkitRepo",
        "https://github.com/$ToolkitRepo.git",
        "git@github.com:$ToolkitRepo",
        "git@github.com:$ToolkitRepo.git"
    )
    if ($Origin -notin $AllowedOrigins) {
        throw "Existing checkout has an unexpected origin: $Origin"
    }
    if ((& git -C $ToolkitSourceDir status --porcelain)) {
        throw "Managed checkout has local changes; review them before updating $ToolkitSourceDir"
    }
    & git -C $ToolkitSourceDir fetch origin $ToolkitChannel
    if ($LASTEXITCODE -ne 0) { throw "Unable to fetch $ToolkitChannel." }
    $CurrentHead = (& git -C $ToolkitSourceDir rev-parse HEAD).Trim()
    & git -C $ToolkitSourceDir merge-base --is-ancestor $CurrentHead FETCH_HEAD
    $CanFastForward = $LASTEXITCODE -eq 0
    if ($CurrentHead -eq $ToolkitLegacyRoot -and -not $CanFastForward) {
        $Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
        $LegacyBackup = "$ToolkitSourceDir.legacy-$Stamp-$PID"
        Write-Host "Agent Toolkit setup: preserving the legacy checkout at $LegacyBackup"
        Move-Item -LiteralPath $ToolkitSourceDir -Destination $LegacyBackup
        & git clone --depth 1 --branch $ToolkitChannel $ToolkitRepoUrl $ToolkitSourceDir
        if ($LASTEXITCODE -ne 0) { throw "Unable to clone the replacement Agent Toolkit checkout." }
    } else {
        $CurrentBranch = (& git -C $ToolkitSourceDir branch --show-current).Trim()
        & git -C $ToolkitSourceDir show-ref --verify --quiet "refs/heads/$ToolkitChannel"
        $TargetBranchExists = $LASTEXITCODE -eq 0
        if ($CurrentBranch -eq $ToolkitChannel) {
            & git -C $ToolkitSourceDir merge --ff-only FETCH_HEAD
        } elseif ($TargetBranchExists) {
            & git -C $ToolkitSourceDir checkout $ToolkitChannel
            & git -C $ToolkitSourceDir merge --ff-only FETCH_HEAD
        } else {
            & git -C $ToolkitSourceDir checkout -b $ToolkitChannel FETCH_HEAD
        }
        if ($LASTEXITCODE -ne 0) { throw "Unable to fast-forward the managed checkout." }
        $CurrentHead = (& git -C $ToolkitSourceDir rev-parse HEAD).Trim()
        $FetchedHead = (& git -C $ToolkitSourceDir rev-parse FETCH_HEAD).Trim()
        if ($CurrentHead -ne $FetchedHead) {
            throw "Managed checkout does not exactly match origin/$ToolkitChannel; refusing to execute local changes."
        }
    }
} elseif (Test-Path $ToolkitSourceDir) {
    if (Get-ChildItem -Force $ToolkitSourceDir | Select-Object -First 1) {
        throw "Source directory exists and is not an Agent Toolkit checkout: $ToolkitSourceDir"
    }
    & git clone --depth 1 --branch $ToolkitChannel $ToolkitRepoUrl $ToolkitSourceDir
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $ToolkitSourceDir -Parent) | Out-Null
    & git clone --depth 1 --branch $ToolkitChannel $ToolkitRepoUrl $ToolkitSourceDir
}
if ($LASTEXITCODE -ne 0) { throw "Unable to prepare the Agent Toolkit checkout." }

$EntryPoint = Join-Path $ToolkitSourceDir "bin/agent-kit"
$VersionCheck = @($PythonPrefix) + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'Python 3.10 or newer is required')")
& $PythonExecutable @VersionCheck
if ($LASTEXITCODE -ne 0) { throw "Python 3.10 or newer is required." }
$StateFile = Join-Path $HOME ".agent-toolkit\state.json"
if (-not $ActionWasExplicit -and (Test-Path $StateFile -PathType Leaf)) {
    try {
        $State = Get-Content -Raw -LiteralPath $StateFile | ConvertFrom-Json
        $ClientEntries = @($State.clients.PSObject.Properties.Value)
        if ($ClientEntries.Count -gt 0 -and @($ClientEntries | Where-Object { $_.status -ne "active" }).Count -eq 0) {
            $Action = "update"
            Write-Host "Agent Toolkit setup: existing installation found; refreshing it."
        }
    } catch {
        throw "Existing Agent Toolkit state is unreadable. Run the explicit doctor command for details."
    }
}
$BaseArgs = @($EntryPoint)
if ($Action -eq "install") {
    $BaseArgs += @("install", "--source", "github", "--repo", $ToolkitRepo, "--channel", $ToolkitChannel)
} else {
    $BaseArgs += $Action
}
$BaseArgs += $AgentKitArgs

& $PythonExecutable @PythonPrefix @BaseArgs
if ($LASTEXITCODE -ne 0) {
    throw "Agent Toolkit command failed with exit code $LASTEXITCODE."
}
if ($Action -in @("install", "update") -and $AgentKitArgs -notcontains "--dry-run") {
    & $PythonExecutable @PythonPrefix $EntryPoint doctor
    if ($LASTEXITCODE -ne 0) {
        throw "Agent Toolkit installed but its final health check failed with exit code $LASTEXITCODE."
    }
}
