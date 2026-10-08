param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$taskProjectRoot = $PSScriptRoot
$taskVenv = Join-Path $taskProjectRoot '.venv'
$taskVenvPython = Join-Path $taskVenv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskVenvPython)) {
    & $Python -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or later is required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
    & $Python -m venv $taskVenv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local virtual environment.' }
}
& $taskVenvPython -m pip install -r (Join-Path $taskProjectRoot 'tools\requirements.txt') 'platformio>=6.1,<7'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
$taskLocalConfig = Join-Path $taskProjectRoot 'tools\aim_host.json'
if (-not (Test-Path -LiteralPath $taskLocalConfig)) {
    Copy-Item -LiteralPath (Join-Path $taskProjectRoot 'tools\aim_host.example.json') -Destination $taskLocalConfig
}
Write-Output 'Setup complete. Build with .\.venv\Scripts\python.exe -m platformio run -e esp32p4-release'
Write-Output 'Local configuration: tools/aim_host.json (ignored by Git). No hardware was flashed.'