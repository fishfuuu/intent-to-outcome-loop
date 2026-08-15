<#
collect_windows_context.ps1

Read-only Windows environment evidence collector for the windows-shell-safe
skill. Compatible with Windows PowerShell 5.1 and PowerShell 7.

Gathers diagnostic evidence only:
  - PowerShell edition / version / executable path
  - host process identity and current working directory
  - resolution of one caller-specified executable (Get-Command)
  - existence / full path / type / reparse attributes of one caller-specified
    target path

It does NOT write files, does NOT change the registry, does NOT access the
network, and does NOT execute or start any command supplied by the caller.
Every cmdlet used here is read-only (Get-*, Test-Path, [Environment]::...).

Output: a single JSON object written to stdout as UTF-8 (no BOM), safely
readable from both editions. Environment facts are evidence; they are never
an execution authorization.

Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File collect_windows_context.ps1 `
        -Executable bash -Target 'C:\repo\target'
#>

[CmdletBinding()]
param(
    [string]$Executable = "",
    [string]$Target = "",
    [string]$WorkingDirectory = ""
)

$ErrorActionPreference = 'Stop'
$WarningPreference = 'SilentlyContinue'

function Get-JsonString {
    param($Value)
    if ($null -eq $Value) { return "" }
    return [string]$Value
}

# Ensure stdout bytes are UTF-8 (no BOM) in both Windows PowerShell 5.1 and
# PowerShell 7. This is a process-level console setting, not a file/registry/
# network mutation.
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = $utf8NoBom
    $stdout = New-Object System.IO.StreamWriter([Console]::OpenStandardOutput(), $utf8NoBom)
    [Console]::SetOut($stdout)
} catch {
    # Best effort; fall back to host defaults if the console is unusual.
}

# ---------------------------------------------------------------------------
# Environment block
# ---------------------------------------------------------------------------
$envBlock = [ordered]@{
    ps_edition               = Get-JsonString $PSVersionTable.PSEdition
    ps_version               = Get-JsonString $PSVersionTable.PSVersion
    ps_major                 = ""
    current_process_path     = ""
    ps_home                  = Get-JsonString $PSHOME
    host_name                = ""
    host_version             = ""
    process_id               = $PID
    working_directory        = ""
    process_current_directory = ""
    windows_apps_dir         = ""
    windows_apps_exists      = $false
    current_process_in_windows_apps = $false
    requested_working_directory = ""
    requested_working_directory_exists = $null
    error                    = ""
}

if ($PSVersionTable.PSVersion) {
    $envBlock.ps_major = Get-JsonString $PSVersionTable.PSVersion.Major
}

try {
    $proc = Get-Process -Id $PID -ErrorAction Stop
    if ($proc) { $envBlock.current_process_path = Get-JsonString $proc.Path }
} catch {
    $envBlock.error = "current process path unavailable: $($_.Exception.Message)"
}

try {
    if ($Host) {
        $envBlock.host_name = Get-JsonString $Host.Name
        $envBlock.host_version = Get-JsonString $Host.Version
    }
} catch {
    $envBlock.error = "host identity unavailable: $($_.Exception.Message)"
}

try {
    $envBlock.working_directory = Get-JsonString (Get-Location).Path
} catch {}

try {
    $envBlock.process_current_directory = Get-JsonString ([Environment]::CurrentDirectory)
} catch {}

try {
    if ($env:LOCALAPPDATA) {
        $wa = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'
        $envBlock.windows_apps_dir = $wa
        $envBlock.windows_apps_exists = Test-Path -LiteralPath $wa
        $cur = $envBlock.current_process_path
        if ($cur -and $wa) {
            $envBlock.current_process_in_windows_apps =
                $cur.StartsWith($wa, [System.StringComparison]::OrdinalIgnoreCase)
        }
    }
} catch {
    $envBlock.error = "windows apps directory unavailable: $($_.Exception.Message)"
}

if ($WorkingDirectory -ne "") {
    try {
        $envBlock.requested_working_directory = Get-JsonString $WorkingDirectory
        $envBlock.requested_working_directory_exists =
            (Test-Path -LiteralPath $WorkingDirectory)
    } catch {
        $envBlock.requested_working_directory_exists = $null
        $envBlock.error = "requested working directory unresolved: $($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------------------
# Executable block
# ---------------------------------------------------------------------------
$execBlock = [ordered]@{
    requested       = Get-JsonString $Executable
    found           = $false
    command_type    = ""
    name            = ""
    resolved_path   = ""
    source          = ""
    version         = ""
    in_windows_apps = $false
    error           = ""
}

if ($Executable -ne "") {
    try {
        $cmd = Get-Command -Name $Executable -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($cmd) {
            $execBlock.found = $true
            $execBlock.command_type = Get-JsonString $cmd.CommandType
            $execBlock.name = Get-JsonString $cmd.Name
            $src = $null
            try { $src = $cmd.Source } catch {}
            if (-not $src) { try { $src = $cmd.Path } catch {} }
            $execBlock.source = Get-JsonString $src
            $execBlock.resolved_path = Get-JsonString $src
            try { $execBlock.version = Get-JsonString $cmd.Version } catch {}
            if ($src -and $envBlock.windows_apps_dir) {
                $execBlock.in_windows_apps =
                    $src.StartsWith($envBlock.windows_apps_dir,
                                    [System.StringComparison]::OrdinalIgnoreCase)
            }
        }
    } catch {
        $execBlock.error = "executable resolution failed: $($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------------------
# Target block
# ---------------------------------------------------------------------------
$targetBlock = [ordered]@{
    requested         = Get-JsonString $Target
    full_path         = ""
    exists            = $false
    item_type         = ""
    attributes        = ""
    is_reparse_point  = $false
    link_type         = ""
    link_target       = ""
    error             = ""
}

if ($Target -ne "") {
    try {
        $full = [System.IO.Path]::GetFullPath($Target)
        $targetBlock.full_path = $full
        $item = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue
        if ($item) {
            $targetBlock.exists = $true
            $targetBlock.item_type = if ($item.PSIsContainer) { "Directory" } else { "File" }
            $targetBlock.attributes = Get-JsonString $item.Attributes
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                $targetBlock.is_reparse_point = $true
            }
            try {
                $targetBlock.link_type = Get-JsonString $item.LinkType
                $targetBlock.link_target = Get-JsonString $item.Target
            } catch {}
        }
    } catch {
        $targetBlock.exists = $false
        $targetBlock.error = "target resolution failed: $($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------
$result = [ordered]@{
    collector_version = "0.2.0"
    schema            = "windows-context-v1"
    environment       = $envBlock
    executable        = $execBlock
    target            = $targetBlock
}

try {
    $json = $result | ConvertTo-Json -Depth 12 -Compress
} catch {
    $json = '{"collector_version":"0.2.0","schema":"windows-context-v1","error":"serialization failed: ' +
        (Get-JsonString $_.Exception.Message).Replace('"', "'") + '"}'
}

try {
    # Write a bare LF terminator (not Environment.NewLine, which is CRLF on
    # Windows) so the JSON line stays clean for downstream consumers.
    [Console]::Out.Write($json + "`n")
    $stdout.Flush()
} catch {
    Write-Output $json
}
