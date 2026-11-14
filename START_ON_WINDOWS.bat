@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency install failed. Please check Python and your internet connection.
  pause
  exit /b 1
)
python -m streamlit run app.py
pause
