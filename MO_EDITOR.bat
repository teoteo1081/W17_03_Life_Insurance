@echo off
rem Bam dup file nay de mo editor portfolio. Giu cua so nay mo trong luc sua.
chcp 65001 >nul
title Editor Portfolio - giu cua so nay mo khi dang sua
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 dev_server.py --open
) else (
  python dev_server.py --open
)
echo.
echo May chu da dung. Bam phim bat ky de dong cua so.
pause >nul
