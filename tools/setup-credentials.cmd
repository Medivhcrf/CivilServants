@echo off
rem One-time credential setup for git push. Paste your GitHub token when asked.
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-credentials.ps1" %*
echo.
pause
exit /b %ERRORLEVEL%
