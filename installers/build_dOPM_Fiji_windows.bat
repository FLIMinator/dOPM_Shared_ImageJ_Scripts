@echo off
setlocal EnableExtensions EnableDelayedExpansion
title dOPM Fiji 2.9.0 environment builder

rem ============================================================================
rem Reproducible dOPM Fiji environment builder - Windows 64-bit
rem
rem No Python installation is required.
rem Requires the curl.exe and tar.exe included with current Windows versions.
rem
rem This script builds the Fiji environment that passed the dOPM faithful
rem end-to-end validation workflow. It DOES NOT install the dOPM Jython scripts.
rem Copy this repository's production .py files separately to:
rem   Fiji.app\plugins\Scripts\dOPM
rem ============================================================================

cd /d "%~dp0"

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"
set "ROOT=%REPO_ROOT%\Fiji_2.9.0_dOPM"
set "FIJI=%ROOT%\Fiji.app"
set "WORK=%TEMP%\dopm_fiji_2_9_0_build"

set "FIJI_URL=https://downloads.imagej.net/fiji/releases/2.9.0/fiji-2.9.0-win64.zip"
set "BIGSTITCHER_URL=https://sites.imagej.net/BigStitcher/plugins/Big_Stitcher-0.8.3.jar-20211130143242"
set "BDV_CORE_URL=https://sites.imagej.net/Fiji/jars/bigdataviewer-core-10.2.0.jar-20210222164216"
set "BDV_VISTOOLS_URL=https://sites.imagej.net/Fiji/jars/bigdataviewer-vistools-1.0.0-beta-28.jar-20210222164216"
set "BDV_FIJI_URL=https://sites.imagej.net/Fiji/plugins/bigdataviewer_fiji-6.2.1.jar-20210222164216"
set "MVR_URL=https://sites.imagej.net/BigStitcher/plugins/multiview_reconstruction-0.11.5.jar-20211201080417"
set "SPIM_URL=https://sites.imagej.net/BigStitcher/plugins/SPIM_Registration-0.0.1.jar-20180411172036"
set "CLIJ_URL=https://sites.imagej.net/clij/plugins/clij_-1.9.0.1.jar-20210613085830"
set "CLIJ2_URL=https://sites.imagej.net/clij2/plugins/clij2_-2.5.1.4.jar-20211023172143"
set "CLEARCL_URL=https://repo1.maven.org/maven2/net/haesleinhuepf/clij-clearcl/2.5.0.1/clij-clearcl-2.5.0.1.jar"
set "CLIJCORE_URL=https://repo1.maven.org/maven2/net/haesleinhuepf/clij-core/1.8.1.1/clij-core-1.8.1.1.jar"
set "COREMEM_URL=https://repo1.maven.org/maven2/net/haesleinhuepf/clij-coremem/2.3.0.4/clij-coremem-2.3.0.4.jar"
set "JOCL_URL=https://repo1.maven.org/maven2/org/jocl/jocl/2.0.2/jocl-2.0.2.jar"

echo.
echo ============================================================================
echo dOPM Fiji 2.9.0 reproducible environment builder - Windows 64-bit
echo ============================================================================
echo.
echo No CPython/Python installation is required.
echo Output: %ROOT%
echo.

where curl.exe >nul 2>nul
if errorlevel 1 (
    echo [ERROR] curl.exe was not found.
    pause
    exit /b 1
)

where tar.exe >nul 2>nul
if errorlevel 1 (
    echo [ERROR] tar.exe was not found.
    pause
    exit /b 1
)

if exist "%ROOT%" (
    echo Existing build found.
    choice /C YN /N /M "Delete it and rebuild from scratch? [Y/N] "
    if errorlevel 2 exit /b 0
    rmdir /S /Q "%ROOT%"
    if exist "%ROOT%" (
        echo [ERROR] Could not remove the previous build.
        echo Close Fiji and any Explorer windows using that folder, then try again.
        pause
        exit /b 1
    )
)

if exist "%WORK%" rmdir /S /Q "%WORK%"
mkdir "%WORK%" || goto :fail
mkdir "%ROOT%" || goto :fail

echo.
echo [1/13] Downloading official Fiji 2.9.0 win64...
curl.exe -L --fail --retry 3 --output "%WORK%\fiji.zip" "%FIJI_URL%"
if errorlevel 1 goto :fail

echo.
echo [2/13] Extracting Fiji...
tar.exe -xf "%WORK%\fiji.zip" -C "%ROOT%"
if errorlevel 1 goto :fail
if not exist "%FIJI%\ImageJ-win64.exe" (
    echo [ERROR] Fiji extracted but ImageJ-win64.exe was not found.
    goto :fail
)

echo.
echo [3/13] Pinning BigDataViewer compatibility stack...
for %%F in ("%FIJI%\jars\bigdataviewer-core*.jar") do if exist "%%~fF" del /Q "%%~fF"
for %%F in ("%FIJI%\jars\bigdataviewer-vistools*.jar") do if exist "%%~fF" del /Q "%%~fF"
for %%F in ("%FIJI%\plugins\bigdataviewer_fiji*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\bigdataviewer-core-10.2.0.jar" "%BDV_CORE_URL%"
if errorlevel 1 goto :fail
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\bigdataviewer-vistools-1.0.0-beta-28.jar" "%BDV_VISTOOLS_URL%"
if errorlevel 1 goto :fail
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\bigdataviewer_fiji-6.2.1.jar" "%BDV_FIJI_URL%"
if errorlevel 1 goto :fail

echo.
echo [4/13] Pinning BigStitcher 0.8.3...
for %%F in ("%FIJI%\plugins\Big_Stitcher*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\Big_Stitcher-0.8.3.jar" "%BIGSTITCHER_URL%"
if errorlevel 1 goto :fail

echo.
echo [5/13] Installing Multiview Reconstruction 0.11.5...
for %%F in ("%FIJI%\plugins\multiview_reconstruction*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\multiview_reconstruction-0.11.5.jar" "%MVR_URL%"
if errorlevel 1 goto :fail

echo.
echo [6/13] Installing SPIM Registration compatibility JAR 0.0.1...
for %%F in ("%FIJI%\plugins\SPIM_Registration*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\SPIM_Registration-0.0.1.jar" "%SPIM_URL%"
if errorlevel 1 goto :fail

echo.
echo [7/13] Installing CLIJ 1.9.0.1...
for %%F in ("%FIJI%\plugins\clij_*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\clij_-1.9.0.1.jar" "%CLIJ_URL%"
if errorlevel 1 goto :fail

echo.
echo [8/13] Installing CLIJ2 2.5.1.4...
for %%F in ("%FIJI%\plugins\clij2_*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\plugins\clij2_-2.5.1.4.jar" "%CLIJ2_URL%"
if errorlevel 1 goto :fail

echo.
echo [9/13] Installing CLIJ Java dependencies...
for %%F in ("%FIJI%\jars\clij-clearcl*.jar") do if exist "%%~fF" del /Q "%%~fF"
for %%F in ("%FIJI%\jars\clij-core-*.jar") do if exist "%%~fF" del /Q "%%~fF"
for %%F in ("%FIJI%\jars\clij-coremem*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\clij-clearcl-2.5.0.1.jar" "%CLEARCL_URL%"
if errorlevel 1 goto :fail
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\clij-core-1.8.1.1.jar" "%CLIJCORE_URL%"
if errorlevel 1 goto :fail
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\clij-coremem-2.3.0.4.jar" "%COREMEM_URL%"
if errorlevel 1 goto :fail

echo.
echo [10/13] Installing JOCL 2.0.2 for CLIJ/OpenCL...
for %%F in ("%FIJI%\jars\jocl-*.jar") do if exist "%%~fF" del /Q "%%~fF"
curl.exe -L --fail --retry 3 --output "%FIJI%\jars\jocl-2.0.2.jar" "%JOCL_URL%"
if errorlevel 1 goto :fail

echo.
echo [11/13] Verifying installed components...
set "BAD=0"
call :check "%FIJI%\jars\bigdataviewer-core-10.2.0.jar" "BigDataViewer core 10.2.0"
call :check "%FIJI%\jars\bigdataviewer-vistools-1.0.0-beta-28.jar" "BigDataViewer vistools beta-28"
call :check "%FIJI%\plugins\bigdataviewer_fiji-6.2.1.jar" "BigDataViewer Fiji 6.2.1"
call :check "%FIJI%\plugins\Big_Stitcher-0.8.3.jar" "BigStitcher 0.8.3"
call :check "%FIJI%\plugins\multiview_reconstruction-0.11.5.jar" "Multiview Reconstruction 0.11.5"
call :check "%FIJI%\plugins\SPIM_Registration-0.0.1.jar" "SPIM Registration 0.0.1"
call :check "%FIJI%\plugins\clij_-1.9.0.1.jar" "CLIJ 1.9.0.1"
call :check "%FIJI%\plugins\clij2_-2.5.1.4.jar" "CLIJ2 2.5.1.4"
call :check "%FIJI%\jars\clij-clearcl-2.5.0.1.jar" "CLIJ ClearCL 2.5.0.1"
call :check "%FIJI%\jars\clij-core-1.8.1.1.jar" "CLIJ core 1.8.1.1"
call :check "%FIJI%\jars\clij-coremem-2.3.0.4.jar" "CLIJ coremem 2.3.0.4"
call :check "%FIJI%\jars\jocl-2.0.2.jar" "JOCL 2.0.2"
if exist "%FIJI%\jars\bigdataviewer-core-10.4.3.jar" (
    echo   [FAIL] Incompatible BigDataViewer core 10.4.3 is still present
    set "BAD=1"
)
if "%BAD%"=="1" goto :fail

echo.
echo [12/13] Writing environment record...
(
    echo dOPM Fiji reproducible environment
    echo Base: official Fiji 2.9.0 win64
    echo.
    echo Added/replaced components:
    echo bigdataviewer-core-10.2.0.jar
    echo bigdataviewer-vistools-1.0.0-beta-28.jar
    echo bigdataviewer_fiji-6.2.1.jar
    echo Big_Stitcher-0.8.3.jar
    echo multiview_reconstruction-0.11.5.jar
    echo SPIM_Registration-0.0.1.jar
    echo clij_-1.9.0.1.jar
    echo clij2_-2.5.1.4.jar
    echo clij-clearcl-2.5.0.1.jar
    echo clij-core-1.8.1.1.jar
    echo clij-coremem-2.3.0.4.jar
    echo jocl-2.0.2.jar
    echo.
    echo dOPM Jython scripts are NOT installed by this BAT.
    echo Copy the repository production scripts to:
    echo Fiji.app\plugins\Scripts\dOPM
) > "%ROOT%\DOPM_FIJI_ENVIRONMENT.txt"

echo.
echo [13/13] Finalising build...
rmdir /S /Q "%WORK%" >nul 2>nul

echo.
echo ============================================================================
echo BUILD COMPLETE
echo ============================================================================
echo Fiji: %FIJI%
echo.
echo Next:
echo   1. Copy the dOPM repository production scripts into:
echo      %FIJI%\plugins\Scripts\dOPM
echo   2. Launch Fiji.
echo   3. Run validation\Test_dOPM_EndToEnd_v3_faithful.py on the test dataset.
echo   4. Do NOT run Help ^> Update before validation.
echo.
if /I "%DOPM_NO_LAUNCH%"=="1" goto :done
choice /C YN /N /M "Launch Fiji now? [Y/N] "
if errorlevel 2 goto :done
start "" "%FIJI%\ImageJ-win64.exe"

:done
pause
exit /b 0

:check
if exist "%~1" (
    for %%Z in ("%~1") do (
        if %%~zZ GTR 0 (
            echo   [PASS] %~2
        ) else (
            echo   [FAIL] %~2 - zero-byte file
            set "BAD=1"
        )
    )
) else (
    echo   [FAIL] %~2 - missing
    set "BAD=1"
)
exit /b 0

:fail
echo.
echo ============================================================================
echo BUILD FAILED
echo ============================================================================
echo Review the first error above.
if exist "%WORK%" rmdir /S /Q "%WORK%" >nul 2>nul
pause
exit /b 1
