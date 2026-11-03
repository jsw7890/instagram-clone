#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendUrl = "http://localhost:8000"
$FrontendUrl = "http://localhost:5173"

function Write-Step($message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

function Test-Listening([int]$Port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(400)
        if ($ok -and $client.Connected) {
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Wait-Listening([int]$Port, [int]$Seconds = 90) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Listening $Port) { return $true }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

function Find-Command($Name) {
    return (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonLauncher {
    $py = Find-Command "py"
    if ($py) {
        & $py.Source -3 --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @{ Exe = $py.Source; Prefix = @("-3") }
        }
    }
    $python = Find-Command "python"
    if ($python) {
        & $python.Source --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @{ Exe = $python.Source; Prefix = @() }
        }
    }
    throw "Python 3이 없습니다. https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행하세요. (설치 시 Add python.exe to PATH 체크)"
}

function Invoke-Python($Launcher, [string[]]$Args, [string]$WorkDir) {
    $all = @()
    if ($Launcher.Prefix) { $all += $Launcher.Prefix }
    $all += $Args
    if ($WorkDir) {
        Push-Location $WorkDir
        try { & $Launcher.Exe @all } finally { Pop-Location }
    } else {
        & $Launcher.Exe @all
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Python 명령이 실패했습니다: $($all -join ' ')"
    }
}

Write-Host "Instagram 클론 원클릭 실행" -ForegroundColor Green
Write-Host "프로젝트: $Root"

if (-not (Find-Command "npm")) {
    throw "Node.js(npm)가 없습니다. https://nodejs.org/ 에서 LTS를 설치한 뒤 다시 실행하세요."
}

$python = Get-PythonLauncher
$venvPython = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Step "환경 파일 준비"
$backendEnv = Join-Path $Backend ".env"
$frontendEnv = Join-Path $Frontend ".env"
if (-not (Test-Path $backendEnv)) {
    Copy-Item (Join-Path $Backend ".env.example") $backendEnv
    Write-Host "backend/.env 생성"
}
if (-not (Test-Path $frontendEnv)) {
    Copy-Item (Join-Path $Frontend ".env.example") $frontendEnv
    Write-Host "frontend/.env 생성"
}

Write-Step "백엔드 패키지 설치"
if (-not (Test-Path $venvPython)) {
    Write-Host "가상환경 생성 중..."
    Invoke-Python $python @("-m", "venv", ".venv") $Backend
}
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip 업그레이드 실패" }
& $venvPython -m pip install -r (Join-Path $Backend "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "백엔드 패키지 설치 실패" }

Write-Step "프론트엔드 패키지 설치"
Push-Location $Frontend
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install 실패" }
} finally {
    Pop-Location
}

Write-Step "서버 실행"
if (Test-Listening 8000) {
    Write-Host "백엔드가 이미 8000 포트에서 실행 중입니다."
} else {
    Start-Process -FilePath "cmd.exe" -WorkingDirectory $Backend -ArgumentList @(
        "/k",
        "title Instagram Backend && `"$venvPython`" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    )
}

if (Test-Listening 5173) {
    Write-Host "프론트엔드가 이미 5173 포트에서 실행 중입니다."
} else {
    Start-Process -FilePath "cmd.exe" -WorkingDirectory $Frontend -ArgumentList @(
        "/k",
        "title Instagram Frontend && npm run dev"
    )
}

Write-Step "서버 준비 대기"
if (-not (Wait-Listening 8000 90)) {
    throw "백엔드(http://localhost:8000)가 시간 안에 뜨지 않았습니다. 'Instagram Backend' 창 로그를 확인하세요."
}
if (-not (Wait-Listening 5173 90)) {
    throw "프론트엔드(http://localhost:5173)가 시간 안에 뜨지 않았습니다. 'Instagram Frontend' 창 로그를 확인하세요."
}

Write-Step "브라우저 열기"
Start-Process $FrontendUrl

Write-Host ""
Write-Host "실행 완료" -ForegroundColor Green
Write-Host "  앱:     $FrontendUrl"
Write-Host "  API:    $BackendUrl/docs"
Write-Host "  계정:   demo / demo1234"
Write-Host "종료하려면 'Instagram Backend', 'Instagram Frontend' 창을 닫으면 됩니다."
