@echo off
rem Make printable handout (docx + PDF) for the task sheet.
rem Output goes to docs/print/ ; today.pdf always points at the latest one.
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0handout.ps1" %*
exit /b %ERRORLEVEL%
