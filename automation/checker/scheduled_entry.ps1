$ErrorActionPreference = 'Stop'

# This file is copied to <project>/automation/checker/.
# Resolve the project from this committed file; never depend on Scheduled Task cwd
# and never execute a detached AppData watcher copy.
$checkerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = [IO.Path]::GetFullPath((Join-Path $checkerDir '..\..'))
$checker = Join-Path $checkerDir 'checker.py'
$configPath = Join-Path $checkerDir 'config.json'

if (-not (Test-Path -LiteralPath $checker)) { exit 20 }
if (-not (Test-Path -LiteralPath $configPath)) { exit 21 }

$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$slug = [string]$config.repository_slug
$branch = if ($config.branch) { [string]$config.branch } else { 'main' }

$python = Get-Command python.exe -ErrorAction SilentlyContinue
$pythonArgs = @()
if (-not $python) {
    $python = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $python) { exit 22 }
    $pythonArgs = @('-3')
}

$rawOutput = & $python.Source @pythonArgs $checker --repo $repo --config $configPath 2>&1
$checkerRc = $LASTEXITCODE
$text = ($rawOutput -join "`n").Trim()

$result = $null
try { $result = $text | ConvertFrom-Json } catch { $result = $null }

# Optional local-checker -> GitHub feedback channel. This writes a commit status,
# not a repository file, so it cannot collide with OpenCode/ChatGPT Git pushes.
# Duplicate status observations are suppressed locally.
if ($config.publish_github_status -eq $true -and $result) {
    $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
    if (-not $gh) { $gh = Get-Command gh -ErrorAction SilentlyContinue }
    if ($gh) {
        $remoteHead = ''
        try { $remoteHead = (& git -C $repo rev-parse "refs/remotes/origin/$branch" 2>$null).Trim() } catch {}
        if ($remoteHead) {
            $statusText = [string]$result.status
            $taskId = [string]$result.task_id
            $ghState = 'error'
            if ($statusText -match '^(ORCA_CONTINUE_SENT|IDLE_ALREADY_CONTINUED|ORCA_OPENCODE_BUSY|READY_CHECK_ONLY|CHECKER_BUSY)$') {
                $ghState = 'pending'
            } elseif ($statusText -match '^IDLE_') {
                $ghState = 'success'
            }

            $repoName = ($slug -split '/')[-1]
            $context = if ($config.github_status_context -and [string]$config.github_status_context -notmatch 'NEW-PROJECT') {
                [string]$config.github_status_context
            } else {
                "local-checker/$repoName"
            }
            $description = if ($taskId) { "$taskId | $statusText" } else { $statusText }
            if ($description.Length -gt 140) { $description = $description.Substring(0, 140) }

            $common = (& git -C $repo rev-parse --git-common-dir).Trim()
            if (-not [IO.Path]::IsPathRooted($common)) { $common = Join-Path $repo $common }
            $runtimeName = (($slug -replace '[^A-Za-z0-9_.-]+','-').Trim('-')) + '-checker'
            $runtime = Join-Path ([IO.Path]::GetFullPath($common)) $runtimeName
            New-Item -ItemType Directory -Force -Path $runtime | Out-Null
            $statusStatePath = Join-Path $runtime 'github_status_state.json'
            $statusKey = "$remoteHead|$ghState|$context|$description"
            $previousKey = ''
            if (Test-Path -LiteralPath $statusStatePath) {
                try { $previousKey = [string]((Get-Content -LiteralPath $statusStatePath -Raw -Encoding UTF8 | ConvertFrom-Json).key) } catch {}
            }

            if ($previousKey -ne $statusKey) {
                & $gh.Source api --method POST "repos/$slug/statuses/$remoteHead" -f "state=$ghState" -f "context=$context" -f "description=$description" 1>$null 2>$null
                if ($LASTEXITCODE -eq 0) {
                    [ordered]@{
                        key = $statusKey
                        posted_at = (Get-Date).ToString('s')
                        sha = $remoteHead
                        state = $ghState
                        context = $context
                        description = $description
                    } | ConvertTo-Json | Set-Content -LiteralPath $statusStatePath -Encoding UTF8
                }
            }
        }
    }
}

# Hidden Scheduled Task does not need console output, but manual invocation remains useful.
if ($text) { Write-Output $text }
exit $checkerRc
