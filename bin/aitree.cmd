@echo off
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv run --no-project python "%~dp0..\scripts\dir_overview.py" %*
) else (
    python "%~dp0..\scripts\dir_overview.py" %*
)
