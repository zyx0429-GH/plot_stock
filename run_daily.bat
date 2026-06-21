@echo off
chcp 65001 >nul
REM 每日盘後更新脚本 — plot_stock
REM 使用方法: 双击运行 或 加入 Windows 排程任务

cd /d "%~dp0"
echo ==========================================
echo Plot Stock Daily Update
echo ==========================================

python scripts\data_fetcher.py
if errorlevel 1 goto error

echo [VALIDATE] Checking data integrity...
python scripts\validate_data.py
if errorlevel 1 goto error

python scripts\stock_screener.py
if errorlevel 1 goto error

python scripts\generate_html.py
if errorlevel 1 goto error

git add -A
git commit -m "daily: auto update %date% %time%"
git push mirror main --force

echo.
echo [OK] Daily update complete!
pause
exit /b 0

:error
echo.
echo [ERROR] Update failed!
pause
exit /b 1
