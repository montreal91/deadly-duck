@echo off
setlocal

cd /d "%~dp0"
call "dd\Scripts\activate.bat"
python main.py

endlocal
