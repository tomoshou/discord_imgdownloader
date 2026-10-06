@echo off
cd /d "%~dp0"
title Discord 画像一括ダウンローダー

if not exist "config.ini" (
    copy "config.example.ini" "config.ini" >nul
    echo.
    echo config.ini を作成しました。
    echo メモ帳が開くので、BOT_TOKEN にトークンを貼り付けて上書き保存してください。
    echo 保存したら、もう一度この run.bat をダブルクリックしてください。
    echo.
    start notepad "config.ini"
    pause
    exit /b
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 discord_img_downloader.py
    goto END
)
where python >nul 2>nul
if %errorlevel%==0 (
    python discord_img_downloader.py
    goto END
)

echo.
echo 【エラー】Python が見つかりません。
echo https://www.python.org/downloads/ から Python をインストールしてください。
echo インストール時に「Add python.exe to PATH」にチェックを入れてください。
echo.

:END
echo.
pause
