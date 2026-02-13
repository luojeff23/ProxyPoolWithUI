param(
    [string]$HttpProxy = "http://127.0.0.1:7890",
    [string]$HttpsProxy = "",
    [switch]$InstallDeps,
    [switch]$InstallHtmlFetchers,
    [switch]$UseVenv
)

if ([string]::IsNullOrWhiteSpace($HttpsProxy)) {
    $HttpsProxy = $HttpProxy
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonCmd = "python"

if ($UseVenv) {
    $venvPath = Join-Path $projectRoot ".venv"
    $venvPython = Join-Path $venvPath "Scripts\\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Host "[step] Creating virtual environment at $venvPath ..."
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    $pythonCmd = $venvPython
}

$env:HTTP_PROXY = $HttpProxy
$env:HTTPS_PROXY = $HttpsProxy
$env:NO_PROXY = "127.0.0.1,localhost"

Write-Host "[proxy] HTTP_PROXY=$($env:HTTP_PROXY)"
Write-Host "[proxy] HTTPS_PROXY=$($env:HTTPS_PROXY)"
Write-Host "[proxy] NO_PROXY=$($env:NO_PROXY)"

if ($InstallDeps) {
    Write-Host "[step] Installing dependencies with proxy..."
    & $pythonCmd -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pythonCmd -m pip install -r (Join-Path $projectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if ($InstallHtmlFetchers) {
        & $pythonCmd -m pip install -r (Join-Path $projectRoot "requirements-html-fetchers.txt")
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Write-Host "[step] Starting ProxyPoolWithUI..."
Push-Location $projectRoot
try {
    & $pythonCmd main.py
} finally {
    Pop-Location
}
