# Installs the /ai-kit skill for this user and the global CLAUDE.md block.
# Run once per machine, and again after pulling the kit to refresh both.
# Usage: ./install.ps1 [-NoGlobalBlock]
param([switch]$NoGlobalBlock)
$ErrorActionPreference = "Stop"

$Kit = $PSScriptRoot
$ClaudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
$SkillDir = Join-Path $ClaudeHome "skills\ai-kit"
$GlobalMd = Join-Path $ClaudeHome "CLAUDE.md"
$Utf8 = New-Object System.Text.UTF8Encoding($false)

New-Item -ItemType Directory -Force $SkillDir | Out-Null
$Reference = Join-Path $SkillDir "reference"
if (Test-Path $Reference) { Remove-Item -Recurse -Force $Reference -Confirm:$false }
Copy-Item -Recurse -Force (Join-Path $Kit "installer\ai-kit\*") $SkillDir
[System.IO.File]::WriteAllText((Join-Path $SkillDir "kit-path"), "$Kit`n", $Utf8)
Write-Output "skill: $SkillDir (kit at $Kit)"

if (-not $NoGlobalBlock) {
    $existing = if (Test-Path $GlobalMd) { [System.IO.File]::ReadAllText($GlobalMd) } else { "" }
    $pattern = '(?s)<!-- ai-kit:start.*?<!-- ai-kit:end -->\r?\n?'
    $kept = [regex]::Replace($existing, $pattern, "").TrimEnd()
    $block = [System.IO.File]::ReadAllText((Join-Path $Kit "global\CLAUDE.md"))
    $content = if ($kept) { "$kept`n`n$block" } else { $block }
    [System.IO.File]::WriteAllText($GlobalMd, $content, $Utf8)
    Write-Output "global block: $GlobalMd"
}

Write-Output "done. In a project, open Claude Code and run: /ai-kit install"
