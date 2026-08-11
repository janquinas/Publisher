@echo off
title Automated Publishing Agent

:MENU
cls
echo.
echo  +----------------------------------------------+
echo  ^|       Automated Publishing Agent            ^|
echo  ^|             Inicializador                   ^|
echo  +----------------------------------------------+
echo.
echo   Escolha o modo de inicializacao:
echo.
echo   [1]  Desenvolvimento  (hot-reload, padrao)
echo   [2]  Producao         (Uvicorn, sem reload)
echo   [3]  Docker           (docker-compose up)
echo   [4]  Parar Docker     (docker-compose down)
echo   [5]  Status           (processos e containers)
echo   [0]  Sair
echo.
set /p OPCAO="  Digite o numero e pressione Enter: "

if "%OPCAO%"=="1" goto DEV
if "%OPCAO%"=="2" goto PROD
if "%OPCAO%"=="3" goto DOCKER
if "%OPCAO%"=="4" goto STOP
if "%OPCAO%"=="5" goto STATUS
if "%OPCAO%"=="0" goto FIM

echo.
echo  Opcao invalida. Tente novamente.
timeout /t 2 > nul
goto MENU

:DEV
cls
echo.
echo  [DEV] Iniciando modo desenvolvimento...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" dev -WorkDir "%~dp0.."
echo.
echo  Servidor encerrado. Pressione qualquer tecla para voltar ao menu...
pause > nul
goto MENU

:PROD
cls
echo.
echo  [PROD] Iniciando modo producao...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" prod -WorkDir "%~dp0.."
echo.
echo  Servidor encerrado. Pressione qualquer tecla para voltar ao menu...
pause > nul
goto MENU

:DOCKER
cls
echo.
echo  [DOCKER] Subindo containers...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" docker -WorkDir "%~dp0.."
echo.
pause
goto MENU

:STOP
cls
echo.
echo  [STOP] Parando containers Docker...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" stop -WorkDir "%~dp0.."
echo.
pause
goto MENU

:STATUS
cls
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" status -WorkDir "%~dp0.."
echo.
pause
goto MENU

:FIM
exit
