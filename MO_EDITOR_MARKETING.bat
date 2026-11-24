@echo off
rem NHANH THU NGHIEM CV DIGITAL MARKETING - khong anh huong web that.
rem Bam dup file nay de mo editor. Giu cua so nay mo trong luc sua.
chcp 65001 >nul
title Editor CV MARKETING (nhanh thu nghiem) - giu cua so nay mo
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul
if %errorlevel%==0 (
  start "" cmd /c "timeout /t 2 >nul & start http://localhost:8020/editor_workspace/editor_cv.html"
  py -3 dev_server.py --port 8020
) else (
  start "" cmd /c "timeout /t 2 >nul & start http://localhost:8020/editor_workspace/editor_cv.html"
  python dev_server.py --port 8020
)
echo.
echo May chu da dung. Bam phim bat ky de dong cua so.
pause >nul
