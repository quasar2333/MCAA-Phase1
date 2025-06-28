@echo off
rem Package the MCAA-Phase1 application using PyInstaller

rem Install PyInstaller if it's not already available
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

rem Create a standalone executable
pyinstaller --onefile --name mcaa_app main.py

rem Inform the user of the output location
if exist dist\mcaa_app.exe (
    echo Package created successfully: dist\mcaa_app.exe
) else (
    echo Packaging failed. See output above for details.
)
