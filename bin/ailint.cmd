@echo off
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv run --no-project python "%~dp0..\scripts\claudemd_linter.py" %*
) else (
    python "%~dp0..\scripts\claudemd_linter.py" %*
)
