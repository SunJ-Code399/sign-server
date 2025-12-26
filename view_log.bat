@echo off
REM 查看最新的日志文件

cd /d %~dp0
set LOG_DIR=%~dp0logs

echo ========================================
echo 查看 Sign Server 日志（实时刷新）
echo 按 Ctrl+C 退出
echo ========================================
echo.

REM 查找最新的日志文件
for /f "delims=" %%i in ('dir /b /o-d "%LOG_DIR%\app_*.log" 2^>nul') do (
    set LATEST_LOG=%LOG_DIR%\%%i
    goto :found
)

:found
if not defined LATEST_LOG (
    echo [错误] 未找到日志文件
    pause
    exit /b 1
)

echo 日志文件: %LATEST_LOG%
echo.

REM 使用PowerShell查看实时日志
powershell -Command "Get-Content '%LATEST_LOG%' -Wait -Tail 50"

