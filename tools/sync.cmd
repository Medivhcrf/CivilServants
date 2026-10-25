@echo off
rem Commit + push with a message you write. Example:
rem   .\tools\sync.cmd "Day 12: summary 8/15"
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync.ps1" %*
exit /b %ERRORLEVEL%
