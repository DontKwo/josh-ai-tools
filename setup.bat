@echo off
setlocal EnableDelayedExpansion

echo =======================================================
echo          Josh's AI Tools Setup for Windows
echo =======================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "CLAUDE_DIR=%USERPROFILE%\.claude"
set "SOURCE_SETTINGS=%SCRIPT_DIR%templates\claude_settings.json"
set "CONFIGURATOR=%SCRIPT_DIR%scripts\configure.py"

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python 3 is not found in your PATH.
    echo     Please install Python 3.9+ to run the setup and linter tools.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [OK] Python detected: !PY_VER!
echo Repo directory: %SCRIPT_DIR%
echo.

echo Choose configuration mode:
echo   [1] Configure Claude Code only (Global ~/.claude/CLAUDE.md)
echo   [2] Configure ALL AI Tools (Claude, Cursor, Cline, Antigravity, Codex, Windsurf, Copilot, Aider)
echo   [3] Custom Interactive Wizard
echo.
choice /C 123 /N /M "Select option [1, 2, or 3]: "
set "MODE_CHOICE=%errorlevel%"

if "%MODE_CHOICE%"=="1" (
    echo.
    echo [+] Configuring Claude Code...
    python "%CONFIGURATOR%" --tools claude --scope global
)
if "%MODE_CHOICE%"=="2" (
    echo.
    echo [+] Configuring ALL supported AI tools...
    python "%CONFIGURATOR%" --tools all --scope global
)
if "%MODE_CHOICE%"=="3" (
    echo.
    python "%CONFIGURATOR%"
)

:: Handle Claude settings.json template if Claude is configured
echo.
set "DEST_SETTINGS=%CLAUDE_DIR%\settings.json"
if exist "%CLAUDE_DIR%" (
    if exist "%DEST_SETTINGS%" (
        echo [?] Claude settings.json already exists at %DEST_SETTINGS%.
        choice /C YN /M "Overwrite existing settings.json with Josh's recommended settings? "
        if errorlevel 1 (
            if not errorlevel 2 (
                copy /y "%SOURCE_SETTINGS%" "%DEST_SETTINGS%" >nul
                echo [OK] settings.json updated.
            )
        )
    ) else (
        choice /C YN /M "Install recommended Claude settings.json (bypassPermissions mode, dark theme)? "
        if not errorlevel 2 (
            copy /y "%SOURCE_SETTINGS%" "%DEST_SETTINGS%" >nul
            echo [OK] settings.json installed.
        )
    )
)

:: Check for optional vulture package
echo.
choice /C YN /M "Install optional 'vulture' package for unused code detection (rule 21)? "
if not errorlevel 2 (
    echo [+] Running: pip install vulture
    pip install vulture
)

:: Global shortcuts in PATH
echo.
choice /C YN /M "Add josh-ai-tools\bin to your User PATH (enables 'ailint', 'aifix', 'airepo', 'aimd', 'aitree', 'aisearch', 'aislice', 'aidiff', 'airollback', 'aisync', 'aitest', 'aitokens', 'aicontext', 'aisec', 'aihook')? "
if not errorlevel 2 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$binPath = '%SCRIPT_DIR%bin'.TrimEnd('\'); " ^
        "$userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); " ^
        "if ($userPath -notlike \"*$binPath*\") { [Environment]::SetEnvironmentVariable('Path', \"$userPath;$binPath\", 'User'); Write-Host '[OK] Added to User PATH!' } else { Write-Host '[OK] Already in User PATH.' }"
)

echo.
echo =======================================================
echo               Setup Completed Successfully!
echo =======================================================
echo All selected AI tools are configured with your rules and linter.
echo.
pause
