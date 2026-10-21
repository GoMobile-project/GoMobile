@echo off
chcp 65001 >nul
title GoMobile - Platform Belajar Siswa & Portal Pengajar
cls
echo ================================================================
echo          GOMOBILE - BIMBINGAN BELAJAR SISWA & PENGAJAR
echo ================================================================
echo.

:: 1. Pindah ke folder proyek GoMobile
cd /d "C:\Users\fajri\Desktop\GoMobile"
if not exist "app.py" (
    echo [ERROR] File app.py tidak ditemukan di C:\Users\fajri\Desktop\GoMobile!
    pause
    exit /b 1
)

:: 2. Cari Python yang terinstall
set "PYTHON_EXE="
if exist "C:\Users\fajri\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYTHON_EXE=C:\Users\fajri\AppData\Local\Programs\Python\Python314\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=py"
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python tidak terdeteksi di laptop Anda!
    echo Silakan install Python terlebih dahulu.
    pause
    exit /b 1
)

echo [1/3] Direktori Proyek : C:\Users\fajri\Desktop\GoMobile
echo [2/3] Python Terdeteksi: %PYTHON_EXE%
echo.
echo [3/3] Server sedang dijalankan...
echo ----------------------------------------------------------------
echo   Website siap diakses di: http://127.0.0.1:5000
echo   Browser akan otomatis terbuka dalam 2 detik...
echo   (JANGAN TUTUP JENDELA HITAM INI SELAMA MEMAKAI WEB)
echo ----------------------------------------------------------------
echo.

:: 3. Buka browser otomatis setelah jeda 2 detik (agar Flask sudah siap)
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

:: 4. Jalankan aplikasi Flask
"%PYTHON_EXE%" app.py

echo.
echo Server telah berhenti.
pause
