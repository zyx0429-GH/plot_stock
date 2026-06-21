@echo off
chcp 65001 >nul
REM 每周六 Norway 数据更新脚本 — plot_stock
REM 使用方法: 每周六下午运行

cd /d "%~dp0"
echo ==========================================
echo Norway Weekly Data Update
echo ==========================================

echo [1/4] Fetching Norway data...
python scripts\norway_fetcher.py
if errorlevel 1 goto error

echo [VALIDATE] Checking Norway data...
python scripts\validate_data.py
if errorlevel 1 goto error

echo [2/4] Updating daily data...
python scripts\data_fetcher.py
if errorlevel 1 goto error

python scripts\stock_screener.py
if errorlevel 1 goto error

python scripts\generate_html.py
if errorlevel 1 goto error

echo [3/4] Generating weekly ranking...
python scripts\norway_to_weekly_json.py
if errorlevel 1 goto error

python scripts\generate_weekly_html.py
if errorlevel 1 goto error

echo [VALIDATE] Final check...
python scripts\validate_data.py
if errorlevel 1 goto error

echo [4/4] Pushing to GitHub...
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
