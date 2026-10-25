@echo off
rem Rebuild the site and publish to GitHub Pages. Double-click safe.
rem   .\tools\publish-site.cmd "commit message"
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish-site.ps1" %*
echo.
pause
exit /b %ERRORLEVEL%
