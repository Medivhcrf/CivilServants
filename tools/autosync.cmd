@echo off
rem Auto commit + push study records. Double-click safe.
rem Uses pwsh when present (reads UTF-8 scripts), falls back to Windows PowerShell.
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0autosync.ps1" %*
exit /b %ERRORLEVEL%
