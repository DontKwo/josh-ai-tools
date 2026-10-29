@echo off
setlocal EnableDelayedExpansion

echo Josh AI Tools Setup for Windows
echo.

set "SCRIPT_DIR=%~dp0"
set "CONFIGURATOR=%SCRIPT_DIR%scripts\configure.py"

:: Check for uv or Python
where uv >nul 2>&1
if %errorlevel% equ 0 (
    set "RUNNER=uv run --no-project python"
    for /f "tokens=*" %%v in ('uv --version 2^>^&1') do echo [OK] uv detected: %%v
) else (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] ERROR: Neither uv nor Python 3 was found in your PATH.
        echo     Please install uv or Python 3.9+ to run setup and linter tools.
        pause
        exit /b 1
    )
    set "RUNNER=python"
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] Python detected: %%v
)

echo Repo directory: %SCRIPT_DIR%
echo.

echo Choose configuration mode:
echo   [1] Configure Claude Code only (Global ~/.claude/CLAUDE.md)
echo   [2] Configure ALL AI Tools globally (Claude, Cursor, Cline, Antigravity, Codex, Windsurf, Copilot, Aider)
echo   [3] Custom Interactive Wizard (choose tools, workspace vs global scope)
echo.
choice /C 123 /M "Select option [1, 2, or 3]"
set "MODE_CHOICE=%errorlevel%"

if "%MODE_CHOICE%"=="1" (
    echo.
    echo [+] Configuring Claude Code...
    call %RUNNER% "%CONFIGURATOR%" --tools claude --scope global
)
if "%MODE_CHOICE%"=="2" (
    echo.
    echo [+] Configuring ALL supported AI tools...
    call %RUNNER% "%CONFIGURATOR%" --tools all --scope global
)
if "%MODE_CHOICE%"=="3" (
    echo.
    call %RUNNER% "%CONFIGURATOR%"
)

if %errorlevel% neq 0 (
    echo.
    echo [!] Configuration encountered an error.
    pause
    exit /b %errorlevel%
)

:: Check for optional vulture package
echo.
choice /C YN /M "Install optional 'vulture' package for unused code detection (used in --level full audits)? "
if not errorlevel 2 (
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        echo [+] Running: uv tool install vulture
        uv tool install vulture
    ) else (
        echo [+] Running: pip install vulture
        pip install vulture
    )
)

:: Global shortcuts in PATH
echo.
choice /C YN /M "Add josh-ai-tools\bin to your User PATH? "
if not errorlevel 2 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$binPath = '%SCRIPT_DIR%bin'.TrimEnd('\'); " ^
        "$userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); " ^
        "$parts = if ($userPath) { $userPath.Split(';') } else { @() }; " ^
        "if ($parts -notcontains $binPath) { $newPath = (($parts + $binPath) -join ';').Trim(';'); [Environment]::SetEnvironmentVariable('Path', $newPath, 'User'); Write-Host '[OK] Added to User PATH!' } else { Write-Host '[OK] Already in User PATH.' }"
    echo [NOTE] Please restart active terminal sessions for the updated PATH to take effect.
)

echo.
echo Setup finished. Selected AI tools configured.
echo.
pause
