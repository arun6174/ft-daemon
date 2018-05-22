@echo off

where /q python
if '%errorlevel%' == '1' (
    echo.
    echo Python 2.7 is not installed im the system.
    echo Download Python 2.7 from here - https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi and install.
    echo.
    @pause
    exit /B
)

:: Get parameters
set action=none
if "%1" == "start" set action=%1
if "%1" == "stop" set action=%1
if "%action%" == "none" (
    echo.
    echo Invalid parameter or parameter missing^!
    echo Usage: %0 ^<start^/stop^>
    echo.
    @pause
    exit /B
)

NET FILE 1>NUL 2>NUL
if not '%errorlevel%' == '0' (
    echo.
    echo You need to run this script as administrator.
    echo Right-click on 'Command Prompt' icon in Start menu and click 'Run as administrator'.
    echo.
    @pause
    exit /B
)

python src/main.py "%action%"
