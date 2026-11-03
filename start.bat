@echo off
setlocal
cd /d "%~dp0"
title Instagram Clone
echo.
echo npm run dev
echo.
call npm run dev
if errorlevel 1 (
  echo.
  echo Start failed.
  pause
  exit /b 1
)
