# ============================================================
#  Automated Publishing Agent - Script de Inicializacao
#  Uso: .\start.ps1 [dev|prod|docker|stop|status|help]
# ============================================================

param(
    [string]$Mode    = "dev",
    [string]$WorkDir = ""
)

# Variavel global para o executavel Python resolvido
$script:PythonExe = $null

# -- Cores ----------------------------------------------------
function Write-Header  { param($msg) Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  [!]   $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red }
function Write-Info    { param($msg) Write-Host "  [..] $msg" -ForegroundColor DarkGray }

# -- Banner ---------------------------------------------------
function Show-Banner {
    Write-Host ""
    Write-Host "  +----------------------------------------------+" -ForegroundColor Magenta
    Write-Host "  |      Automated Publishing Agent              |" -ForegroundColor Magenta
    Write-Host "  |      Modo: $($Mode.ToUpper().PadRight(34))|" -ForegroundColor Magenta
    Write-Host "  +----------------------------------------------+" -ForegroundColor Magenta
    Write-Host ""
}

# -- Ajuda ----------------------------------------------------
function Show-Help {
    Write-Host @"

USO:
    .\start.ps1 [modo]

MODOS:
    dev       Servidor de desenvolvimento com hot-reload (padrao)
    prod      Servidor de producao via Uvicorn
    docker    Sobe os containers com docker-compose
    stop      Para containers Docker em execucao
    status    Mostra o estado atual (processos e containers)
    help      Exibe esta ajuda

EXEMPLOS:
    .\start.ps1
    .\start.ps1 dev
    .\start.ps1 prod
    .\start.ps1 docker
    .\start.ps1 stop
    .\start.ps1 status

"@
}

# -- Resolver executavel Python -------------------------------
function Resolve-Python {
    # Versoes estaveis preferidas primeiro (3.12, 3.11, 3.10), 3.14 como ultimo recurso
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "python",
        "python3",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "C:\Python313\python.exe",
        "C:\Python314\python.exe"
    )

    foreach ($c in $candidates) {
        try {
            $ver = & $c --version 2>&1
            # Ignora o alias da Microsoft Store (nao retorna versao valida)
            if ($ver -match "^Python \d+\.\d+") {
                $script:PythonExe = $c
                return
            }
        } catch {}
    }

    # Ultima tentativa: varrer AppData\Local\Programs\Python
    $pyBase = "$env:LOCALAPPDATA\Programs\Python"
    if (Test-Path $pyBase) {
        $found = Get-ChildItem $pyBase -Directory |
                 Sort-Object Name -Descending |
                 ForEach-Object { "$($_.FullName)\python.exe" } |
                 Where-Object { Test-Path $_ } |
                 Select-Object -First 1
        if ($found) {
            $script:PythonExe = $found
            return
        }
    }

    $script:PythonExe = $null
}

# -- Verificar Python -----------------------------------------
function Assert-Python {
    Write-Info "Verificando Python..."
    Resolve-Python
    if (-not $script:PythonExe) {
        Write-Err "Python nao encontrado. Instale em https://python.org"
        exit 1
    }
    $ver = & $script:PythonExe --version 2>&1
    Write-Success "Python encontrado: $ver  ($($script:PythonExe))"
}

# -- Verificar / criar .env -----------------------------------
function Assert-DotEnv {
    Write-Info "Verificando .env..."
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Warn ".env criado a partir de .env.example - revise as variaveis antes de usar em producao."
        } else {
            Write-Err ".env nao encontrado e .env.example nao existe."
            exit 1
        }
    } else {
        Write-Success ".env encontrado."
    }
}

# -- Verificar / criar venv -----------------------------------
function Assert-Venv {
    Write-Info "Verificando ambiente virtual..."
    if (-not (Test-Path "venv")) {
        Write-Info "Criando ambiente virtual..."
        & $script:PythonExe -m venv venv
        if ($LASTEXITCODE -ne 0) { Write-Err "Falha ao criar venv."; exit 1 }
        Write-Success "Ambiente virtual criado em ./venv"
    } else {
        Write-Success "Ambiente virtual encontrado."
    }
}

# -- Ativar venv ----------------------------------------------
function Enable-Venv {
    $activate = "venv\Scripts\Activate.ps1"
    if (Test-Path $activate) {
        Write-Info "Ativando venv..."
        & $activate
        Write-Success "venv ativado."
    } else {
        Write-Warn "Nao foi possivel ativar o venv automaticamente."
    }
}

# -- Instalar dependencias ------------------------------------
function Install-Deps {
    param([bool]$Prod = $false)
    Write-Info "Instalando dependencias..."
    $pipExe = if (Test-Path "venv\Scripts\pip.exe") { "venv\Scripts\pip.exe" } else { "pip" }
    & $pipExe install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) { Write-Err "Falha ao instalar requirements.txt"; exit 1 }
    if ($Prod) {
        & $pipExe install -r requirements-prod.txt --quiet
        if ($LASTEXITCODE -ne 0) { Write-Err "Falha ao instalar requirements-prod.txt"; exit 1 }
    }
    Write-Success "Dependencias instaladas."
}

# -- Inicializar banco de dados -------------------------------
function Initialize-Database {
    Write-Info "Inicializando banco de dados..."
    if (Test-Path "scripts\init_db.py") {
        $pyExe = if (Test-Path "venv\Scripts\python.exe") { "venv\Scripts\python.exe" } else { $script:PythonExe }
        & $pyExe scripts\init_db.py
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Banco de dados inicializado."
        } else {
            Write-Warn "init_db.py retornou erro - o banco pode ja estar criado ou sera criado no startup."
        }
    } else {
        Write-Warn "scripts\init_db.py nao encontrado - o banco sera criado automaticamente no startup."
    }
}

# -- Verificar porta livre ------------------------------------
function Assert-PortFree {
    param([int]$Port = 8000)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Warn "A porta $Port ja esta em uso. Outro servidor pode estar rodando."
        $resp = Read-Host "  Deseja continuar mesmo assim? (s/N)"
        if ($resp -notmatch "^[sS]$") { exit 0 }
    }
}

# -- Verificar Docker -----------------------------------------
function Assert-Docker {
    Write-Info "Verificando Docker..."
    $d = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $d) {
        Write-Err "Docker nao encontrado. Instale em https://docs.docker.com/get-docker/"
        exit 1
    }
    $dc = Get-Command docker-compose -ErrorAction SilentlyContinue
    if (-not $dc) {
        $dc2 = docker compose version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Err "docker-compose nao encontrado."
            exit 1
        }
    }
    Write-Success "Docker disponivel."
}

# -- Mostrar URL de acesso ------------------------------------
function Show-AccessUrl {
    param([int]$Port = 8000)
    Write-Host ""
    Write-Host "  +---------------------------------------------------+" -ForegroundColor Green
    Write-Host "  |  Aplicacao rodando em:                            |" -ForegroundColor Green
    Write-Host "  |                                                   |" -ForegroundColor Green
    Write-Host "  |   http://localhost:$Port                           |" -ForegroundColor Green
    Write-Host "  |   http://localhost:$Port/app/login.html            |" -ForegroundColor Green
    Write-Host "  |   http://localhost:$Port/docs  (Swagger UI)        |" -ForegroundColor Green
    Write-Host "  |                                                   |" -ForegroundColor Green
    Write-Host "  |   Pressione Ctrl+C para encerrar                  |" -ForegroundColor Green
    Write-Host "  +---------------------------------------------------+" -ForegroundColor Green
    Write-Host ""
}

# ============================================================
#  MODO: DEV
# ============================================================
function Start-Dev {
    Show-Banner
    Write-Header "Iniciando modo DESENVOLVIMENTO..."

    Assert-Python
    Assert-DotEnv
    Assert-Venv
    Enable-Venv
    Install-Deps -Prod $false
    Initialize-Database
    Assert-PortFree -Port 8000
    Show-AccessUrl -Port 8000

    Write-Info "Iniciando servidor com hot-reload..."
    $pyExe = if (Test-Path "venv\Scripts\python.exe") { "venv\Scripts\python.exe" } else { $script:PythonExe }
    & $pyExe -m backend.main
}

# ============================================================
#  MODO: PROD
# ============================================================
function Start-Prod {
    Show-Banner
    Write-Header "Iniciando modo PRODUCAO (Uvicorn)..."

    Assert-Python
    Assert-DotEnv
    Assert-Venv
    Enable-Venv
    Install-Deps -Prod $true
    Initialize-Database
    Assert-PortFree -Port 8000

    $envHost = "0.0.0.0"
    $envPort = 8000
    if (Test-Path ".env") {
        $envLines = Get-Content ".env"
        foreach ($line in $envLines) {
            if ($line -match "^HOST=(.+)$")  { $envHost = $Matches[1].Trim() }
            if ($line -match "^PORT=(\d+)$") { $envPort = [int]$Matches[1].Trim() }
        }
    }

    Show-AccessUrl -Port $envPort
    Write-Info "Iniciando Uvicorn (producao sem reload)..."
    $uvicornExe = if (Test-Path "venv\Scripts\uvicorn.exe") { "venv\Scripts\uvicorn.exe" } else { "uvicorn" }
    & $uvicornExe backend.main:app --host $envHost --port $envPort --workers 1
}

# ============================================================
#  MODO: DOCKER
# ============================================================
function Start-Docker {
    Show-Banner
    Write-Header "Iniciando via Docker Compose..."

    Assert-DotEnv
    Assert-Docker

    Write-Info "Subindo containers (pode demorar na primeira vez)..."
    docker-compose up --build -d

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Falha ao subir containers. Verifique o docker-compose.yml e as variaveis do .env."
        exit 1
    }

    Write-Success "Containers iniciados."
    Write-Host ""
    docker-compose ps
    Show-AccessUrl -Port 8000

    Write-Info "Para ver os logs em tempo real: docker-compose logs -f"
}

# ============================================================
#  MODO: STOP
# ============================================================
function Stop-Docker {
    Show-Banner
    Write-Header "Parando containers Docker..."
    Assert-Docker
    docker-compose down
    Write-Success "Containers parados."
}

# ============================================================
#  MODO: STATUS
# ============================================================
function Show-Status {
    Show-Banner
    Write-Header "Status dos servicos..."

    $proc = Get-Process -Name "python" -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Success "Processo Python rodando (PID: $($proc.Id -join ', '))"
    } else {
        Write-Warn "Nenhum processo Python detectado."
    }

    $conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Success "Porta 8000 em uso (servidor ativo)."
    } else {
        Write-Warn "Porta 8000 livre (servidor nao esta rodando)."
    }

    $d = Get-Command docker -ErrorAction SilentlyContinue
    if ($d) {
        Write-Header "Containers Docker:"
        docker-compose ps 2>&1
    } else {
        Write-Warn "Docker nao instalado - status de containers nao disponivel."
    }
}

# ============================================================
#  ENTRY POINT
# ============================================================

if ($WorkDir -ne "" -and (Test-Path $WorkDir)) {
    Set-Location $WorkDir
} else {
    Set-Location (Split-Path $PSScriptRoot -Parent)
}

switch ($Mode.ToLower()) {
    "dev"    { Start-Dev }
    "prod"   { Start-Prod }
    "docker" { Start-Docker }
    "stop"   { Stop-Docker }
    "status" { Show-Status }
    "help"   { Show-Help }
    default  {
        Write-Err "Modo desconhecido: '$Mode'"
        Show-Help
        exit 1
    }
}
