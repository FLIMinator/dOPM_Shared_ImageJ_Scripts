@echo off
setlocal EnableExtensions EnableDelayedExpansion
title dOPM complete setup - Windows

rem ============================================================================
rem dOPM repository bootstrap - Windows 64-bit
rem
rem This is the recommended one-step setup entry point.
rem
rem It:
rem   1. Builds the pinned Fiji environment if it is not already present.
rem   2. Creates Fiji.app\plugins\Scripts\dOPM.
rem   3. Copies all repository-root .py files into that dOPM plugin folder.
rem   4. Optionally launches Fiji.
rem
rem The repository remains the source of truth: files are COPIED, never moved.
rem No CPython/Python installation is required.
rem ============================================================================

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"
set "INSTALLER=%~dp0build_dOPM_Fiji_windows.bat"
set "FIJI_ROOT=%REPO_ROOT%\Fiji_2.9.0_dOPM"
set "FIJI=%FIJI_ROOT%\Fiji.app"
set "DOPM_DEST=%FIJI%\plugins\Scripts\dOPM"

echo.
echo ============================================================================
echo dOPM complete setup - Windows 64-bit
echo ============================================================================
echo.
echo Repository:
echo   %REPO_ROOT%
echo.
echo Fiji target:
echo   %FIJI%
echo.

if not exist "%INSTALLER%" (
    echo [ERROR] Fiji builder was not found:
    echo   %INSTALLER%
    pause
    exit /b 1
)

if not exist "%FIJI%\ImageJ-win64.exe" (
    echo [1/3] Fiji environment not found. Building it now...
    echo.
    set "DOPM_NO_LAUNCH=1"
    call "%INSTALLER%"
    set "BUILD_RC=!ERRORLEVEL!"
    set "DOPM_NO_LAUNCH="

    if not "!BUILD_RC!"=="0" (
        echo.
        echo [ERROR] Fiji environment builder failed with exit code !BUILD_RC!.
        pause
        exit /b !BUILD_RC!
    )
) else (
    echo [1/3] Existing Fiji environment found; keeping it.
)

if not exist "%FIJI%\ImageJ-win64.exe" (
    echo [ERROR] Fiji executable is still missing after setup:
    echo   %FIJI%\ImageJ-win64.exe
    pause
    exit /b 1
)

echo.
echo [2/3] Creating dOPM Fiji script folder...
if not exist "%DOPM_DEST%" mkdir "%DOPM_DEST%"
if errorlevel 1 (
    echo [ERROR] Could not create:
    echo   %DOPM_DEST%
    pause
    exit /b 1
)

echo.
echo [3/3] Copying repository Python/Jython scripts into Fiji...
set "COPIED=0"
for %%F in ("%REPO_ROOT%\*.py") do (
    if exist "%%~fF" (
        copy /Y "%%~fF" "%DOPM_DEST%\%%~nxF" >nul
        if errorlevel 1 (
            echo [ERROR] Failed to copy %%~nxF
            pause
            exit /b 1
        )
        echo   [COPIED] %%~nxF
        set /A COPIED+=1
    )
)

if "!COPIED!"=="0" (
    echo [ERROR] No repository-root .py files were found to deploy.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo SETUP COMPLETE
echo ============================================================================
echo.
echo Copied !COPIED! Python/Jython files to:
echo   %DOPM_DEST%
echo.
echo Generated Fiji is intentionally outside installers\ and lives at:
echo   %FIJI_ROOT%
echo.
echo The source files in the repository were not moved or modified.
echo.
echo Validation script remains in:
echo   %REPO_ROOT%\validation\Test_dOPM_EndToEnd_v3_faithful.py
echo.

choice /C YN /N /M "Launch Fiji now? [Y/N] "
if errorlevel 2 goto :done
start "" "%FIJI%\ImageJ-win64.exe"

:done
pause
exit /b 0
