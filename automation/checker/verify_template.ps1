$ErrorActionPreference = 'Stop'

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$checker = Join-Path $dir 'checker.py'
$tests = Join-Path $dir 'tests\test_checker.py'
$installer = Join-Path $dir 'install_windows.ps1'
$entry = Join-Path $dir 'scheduled_entry.ps1'

$python = Get-Command python.exe -ErrorAction SilentlyContinue
$pyArgs = @()
if (-not $python) {
    $python = Get-Command py.exe -ErrorAction Stop
    $pyArgs = @('-3')
}

& $python.Source @pyArgs -m py_compile $checker
if ($LASTEXITCODE -ne 0) { throw 'PYTHON_COMPILE_FAILED' }

& $python.Source @pyArgs -m unittest $tests
if ($LASTEXITCODE -ne 0) { throw 'PYTHON_TESTS_FAILED' }

foreach ($ps1 in @($installer, $entry)) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($ps1, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        $message = ($errors | ForEach-Object { $_.Message }) -join '; '
        throw "POWERSHELL_PARSE_FAILED: $ps1 : $message"
    }
}

[ordered]@{
    status = 'PASS'
    python_compile = 'PASS'
    python_tests = 'PASS'
    powershell_install_parse = 'PASS'
    powershell_entry_parse = 'PASS'
} | ConvertTo-Json
