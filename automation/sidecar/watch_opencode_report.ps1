param(
    [string]$RepoPath = 'D:\科研相关\paper\idea\repo',
    [string]$ReportFile = 'OPENCODE_REPORT_AUTORUN.md',
    [switch]$DryRunOnce
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$stateDir = Join-Path $RepoPath 'logs\opencode_watcher'
$statePath = Join-Path $stateDir 'watcher_state.json'
$reportPath = Join-Path $RepoPath $ReportFile

function Write-Log([string]$msg) {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Write-Output "[$ts] $msg"
}

function Load-State {
    if (Test-Path -LiteralPath $statePath) {
        try {
            $raw = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8
            $obj = $raw | ConvertFrom-Json
            if ($obj -and $obj.seen_keys) {
                return @($obj.seen_keys)
            }
        } catch {}
    }
    return @()
}

function Save-State([string[]]$keys) {
    if (-not (Test-Path -LiteralPath $stateDir)) {
        New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    }
    $trimmed = if ($keys.Count -gt 100) { $keys[($keys.Count - 100)..($keys.Count - 1)] } else { $keys }
    $payload = [ordered]@{
        updated_at = (Get-Date).ToString('s')
        seen_keys  = @($trimmed)
    }
    $tmp = "$statePath.tmp"
    $payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $statePath -Force
}

function Parse-Report([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    $text = ''
    for ($i = 0; $i -lt 5; $i++) {
        try {
            $text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
            break
        } catch {
            Start-Sleep -Milliseconds 300
        }
    }
    if (-not $text) { return $null }

    $headers = @{}
    foreach ($line in ($text -split "`r?`n")) {
        if ($line -match '^([A-Z][A-Z0-9_]*)\s*[:=]\s*`?([^`\r\n]+?)`?\s*$') {
            $k = $Matches[1].ToUpperInvariant()
            if (-not $headers.ContainsKey($k)) {
                $headers[$k] = $Matches[2].Trim()
            }
        }
    }

    $sha = [System.BitConverter]::ToString(
        [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($text))
    ).Replace('-', '').ToLowerInvariant()

    return [ordered]@{
        task_id      = [string]$headers['TASK_ID']
        task_version = [string]$headers['TASK_VERSION']
        status       = [string]$headers['STATUS']
        next_actor   = [string]$headers['NEXT_ACTOR']
        sha256       = $sha
    }
}

function Invoke-HandleReport([bool]$isStartupSeed) {
    $info = Parse-Report $reportPath
    if (-not $info) {
        Write-Log "Report not found or unreadable: $reportPath"
        return
    }

    $key = "$($info.task_id)|$($info.task_version)|$($info.sha256)"
    $seen = @(Load-State)

    if ($isStartupSeed -and -not (Test-Path -LiteralPath $statePath)) {
        Save-State @($key)
        Write-Log "Seeded initial state without triggering: task=$($info.task_id) v$($info.task_version) status=$($info.status) next=$($info.next_actor)"
        return
    }

    if ($seen -contains $key) {
        if ($DryRunOnce) { Write-Log "Already handled: $key" }
        return
    }

    if ($info.next_actor -notmatch '^GEMINI\b') {
        Write-Log "Ignored report (NEXT_ACTOR=$($info.next_actor)): task=$($info.task_id) v$($info.task_version)"
        return
    }

    if ($info.status -match '^(PENDING|RUNNING)$') {
        Write-Log "Ignored in-progress status ($($info.status)): task=$($info.task_id)"
        return
    }

    $title = "OpenCode回执: $($info.task_id) ($($info.status))"
    $prompt = "本地 Orca OpenCode 已完成任务 $($info.task_id)（v$($info.task_version)），状态为 $($info.status)，并将 NEXT_ACTOR 交回 GEMINI。请立即阅读 D:\科研相关\paper\idea\repo\OPENCODE_REPORT_AUTORUN.md、对应的子任务报告以及 STAGE_PLAN.md，核验结果并向用户汇报结论与下一步建议。"

    if ($DryRunOnce) {
        Write-Log "DRY_RUN_MATCH: title=$title | key=$key"
        return
    }

    $agentApi = Get-Command agentapi.bat -ErrorAction SilentlyContinue
    if (-not $agentApi) { $agentApi = Get-Command agentapi -ErrorAction SilentlyContinue }
    if (-not $agentApi) {
        Write-Log "ERROR: agentapi not found on PATH"
        return
    }

    Write-Log "Triggering Antigravity conversation: $title"
    & $agentApi.Source new-conversation "--title=$title" $prompt
    $rc = $LASTEXITCODE
    if ($rc -eq 0) {
        Save-State ($seen + $key)
        Write-Log "Triggered successfully (exit 0) and recorded key=$key"
    } else {
        Write-Log "ERROR: agentapi exited with code $rc"
    }
}

if ($DryRunOnce) {
    Invoke-HandleReport -isStartupSeed:$false
    exit 0
}

Write-Log "Starting FileSystemWatcher on $reportPath"
Invoke-HandleReport -isStartupSeed:$true

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $RepoPath
$watcher.Filter = $ReportFile
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::Size
$watcher.EnableRaisingEvents = $true

try {
    while ($true) {
        $change = $watcher.WaitForChanged(
            [System.IO.WatcherChangeTypes]::Changed -bor [System.IO.WatcherChangeTypes]::Created -bor [System.IO.WatcherChangeTypes]::Renamed,
            60000
        )
        if (-not $change.TimedOut) {
            Start-Sleep -Milliseconds 1500
            Invoke-HandleReport -isStartupSeed:$false
        }
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
}
