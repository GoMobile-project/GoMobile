@echo off
chcp 65001 >nul
title GoMobile - Push ke GitHub
cls
echo ================================================================
echo           GOMOBILE - PUSH REPOSITORY KE GITHUB
echo ================================================================
echo.
cd /d "C:\Users\fajri\Desktop\GoMobile"

:: Tambahkan Git ke PATH sesi ini jika belum ada
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\bin;%PATH%"

echo Remote URL : https://github.com/GoMobile-project/GoMobile.git
echo Branch     : main
echo.
echo Melakukan git push...
echo (Jika muncul jendela browser untuk verifikasi akun GitHub, silakan Sign In)
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo [GAGAL / BUTUH LOGIN] Push ke GitHub belum selesai.
    echo Pastikan akun GitHub Anda memiliki hak akses Write/Owner ke GoMobile-project/GoMobile.
) else (
    echo.
    echo ================================================================
    echo [BERHASIL] Seluruh kode GoMobile sukses di-push ke GitHub!
    echo ================================================================
)

echo.
pause
