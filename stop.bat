@echo off
setlocal enabledelayedexpansion

REM 切换到脚本所在目录
cd /d %~dp0

echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║                                                            ║
echo  ║          ■■■ 停止跨境签名程序服务 ■■■                    ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查是否有 Python 进程在运行
echo 正在检查 Python 进程...
tasklist | findstr /I "python.exe py.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo 找到 Python 进程，正在停止...
    echo.

    REM 停止所有 python.exe 进程
    taskkill /IM python.exe /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo  [成功] python.exe 进程已停止
    )

    REM 停止所有 py.exe 进程
    taskkill /IM py.exe /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo  [成功] py.exe 进程已停止
    )

    echo.
    echo  ╔════════════════════════════════════════════════════════════╗
    echo  ║                                                            ║
    echo  ║  [成功] Python 进程已停止                                     ║
    echo  ║                                                            ║
    echo  ╚════════════════════════════════════════════════════════════╝
) else (
    echo.
    echo  ╔════════════════════════════════════════════════════════════╗
    echo  ║                                                            ║
    echo  ║  [信息] 未找到运行中的 Python 进程                        ║
    echo  ║                                                            ║
    echo  ╚════════════════════════════════════════════════════════════╝
)

echo.
timeout /t 2 /nobreak >nul
endlocal
