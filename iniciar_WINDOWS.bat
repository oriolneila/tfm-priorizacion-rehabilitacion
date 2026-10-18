@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Error al instalar dependencias. Comprueba Python 3.10+ y la conexion a internet.
 pause
 exit /b 1
)
python -m streamlit run app.py
pause
