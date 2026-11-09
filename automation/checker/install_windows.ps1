param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$checkerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = [IO.Path]::GetFullPath((Join-Path $checkerDir '..\..'))
$configPath = Join-Path $checkerDir 'config.json'
$examplePath = Join-Path $checkerDir 'config.example.json'
$launcher = Join-Path $checkerDir 'hidden_runner.vbs'
$entry = Join-Path $checkerDir 'scheduled_entry.ps1'
$checker = Join-Path $checkerDir 'checker.py'

foreach ($p in @($checker, $entry, $launcher)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "MISSING_CHECKER_FILE: $p" }
}

if (-not (Test-Path -LiteralPath $configPath)) {
    if (-not (Test-Path -LiteralPath $examplePath)) { throw 'CONFIG_AND_EXAMPLE_MISSING' }
    Copy-Item -LiteralPath $examplePath -Destination $configPath
    throw "CONFIG_CREATED_FROM_EXAMPLE: edit $configPath and rerun installer"
}

$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($config.schema_version -ne 1) { throw 'CONFIG_SCHEMA_VERSION' }
$slug = [string]$config.repository_slug
if ([string]::IsNullOrWhiteSpace($slug) -or $slug -match '/NEW-PROJECT$') { throw 'CONFIG_REPOSITORY_SLUG' }
$branch = if ($config.branch) { [string]$config.branch } else { 'main' }
$minutes = if ($config.poll_minutes) { [int]$config.poll_minutes } else { 10 }
if ($minutes -lt 1) { throw 'CONFIG_POLL_MINUTES' }

$origin = (& git -C $repo remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0) { throw 'GIT_ORIGIN_UNREADABLE' }
$expectedName = ($slug -split '/')[-1]
$taskName = "$expectedName-OpenCode-${minutes}min"

# Validate the checker/config before installing anything.
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source $checker --repo $repo --config $configPath --check
    $checkRc = $LASTEXITCODE
} else {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $py) { throw 'PYTHON_NOT_FOUND' }
    & $py.Source -3 $checker --repo $repo --config $configPath --check
    $checkRc = $LASTEXITCODE
}
if ($checkRc -gt 2) { throw "CHECKER_SELF_CHECK_FAILED:$checkRc" }

$wscript = Join-Path $env:WINDIR 'System32\wscript.exe'
$actionArgs = @{
    Execute = $wscript
    Argument = ("//B //NoLogo `"{0}`"" -f $launcher)
    WorkingDirectory = $checkerDir
}
$action = New-ScheduledTaskAction @actionArgs

$triggerArgs = @{
    Once = $true
    At = (Get-Date).AddMinutes(1)
    RepetitionInterval = (New-TimeSpan -Minutes $minutes)
}
$trigger = New-ScheduledTaskTrigger @triggerArgs

$settingsArgs = @{
    MultipleInstances = 'IgnoreNew'
    StartWhenAvailable = $true
    ExecutionTimeLimit = (New-TimeSpan -Minutes 5)
}
$settings = New-ScheduledTaskSettingsSet @settingsArgs

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and -not $Force) {
    throw "TASK_ALREADY_EXISTS: $taskName (rerun with -Force to replace)"
}
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$registerArgs = @{
    TaskName = $taskName
    Action = $action
    Trigger = $trigger
    Settings = $settings
    Description = "Project-local GitHub -> Orca/OpenCode checker for $slug"
    Force = $true
}
Register-ScheduledTask @registerArgs | Out-Null

$result = [ordered]@{
    status = 'INSTALLED'
    repository = $slug
    repo_path = $repo
    branch = $branch
    task_name = $taskName
    poll_minutes = $minutes
    action = "$wscript //B //NoLogo `"$launcher`""
    checker_source = $checker
    appdata_checker_copy = $false
}
$result | ConvertTo-Json -Depth 4
