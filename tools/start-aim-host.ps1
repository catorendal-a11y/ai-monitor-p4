$ErrorActionPreference = 'Stop'
$taskHostScript = Join-Path $PSScriptRoot 'aim_host.py'
$taskProject = Split-Path $PSScriptRoot -Parent
$taskCandidates = @((Join-Path $taskProject '.venv\Scripts\python.exe'), (Join-Path $env:USERPROFILE '.platformio\penv\Scripts\python.exe'))
$taskFallback = Get-Command python.exe -ErrorAction SilentlyContinue
if ($taskFallback) { $taskCandidates += $taskFallback.Source }
$taskPython = $null
foreach ($taskCandidate in $taskCandidates | Select-Object -Unique) {
    if (-not (Test-Path -LiteralPath $taskCandidate)) { continue }
    try { & $taskCandidate -c 'import serial' 1>$null 2>$null } catch { continue }
    if ($LASTEXITCODE -eq 0) { $taskPython = $taskCandidate; break }
}
if (-not $taskPython) { throw 'Python with pyserial was not found. Install tools/requirements.txt.' }
$taskPythonw = Join-Path (Split-Path $taskPython -Parent) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPythonw)) { $taskPythonw = $taskPython }

# Restart only the host for this exact checkout, including pythonw processes.
$taskHosts = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -and
    $_.CommandLine.Replace('/', '\').IndexOf($taskHostScript, [StringComparison]::OrdinalIgnoreCase) -ge 0
}
foreach ($taskHost in $taskHosts) { Stop-Process -Id $taskHost.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Process -FilePath $taskPythonw -ArgumentList @('"' + $taskHostScript + '"') -WorkingDirectory $taskProject -WindowStyle Hidden
Write-Output 'AI Monitor Host started in the background. Log: tools/aim_host.log'
