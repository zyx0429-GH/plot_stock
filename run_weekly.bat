@echo off
chcp 65001 >nul
REM 每周六 Norway 数据更新脚本 — plot_stock
REM 使用方法: 每周六下午运行

cd /d "%~dp0"
echo ==========================================
echo Norway Weekly Data Update
echo ==========================================

echo [1/3] Fetching Norway data...
python scripts\norway_fetcher.py
if errorlevel 1 goto error

echo [2/3] Updating daily data...
python scripts\data_fetcher.py
if errorlevel 1 goto error

python scripts\stock_screener.py
if errorlevel 1 goto error

python scripts\generate_html.py
if errorlevel 1 goto error

echo [3/3] Pushing to GitHub...
git add -A
git commit -m "weekly: Norway update %date%"
git push mirror main --force

echo.
echo [OK] Weekly update complete!
pause
exit /b 0

:error
echo.
echo [ERROR] Update failed!
pause
exit /b 1
