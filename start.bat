@echo off
setlocal enabledelayedexpansion

REM 切换到脚本所在目录（自动获取项目根目录）
cd /d %~dp0
set PROJECT_DIR=%CD%
set LOG_DIR=%PROJECT_DIR%\logs
if errorlevel 1 (
    echo [错误] 无法切换到项目目录: %PROJECT_DIR%
    pause
    exit /b 1
)

REM 检查Python是否安装（优先使用python，因为pythonw可能不存在）
set PYTHON_CMD=py
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到Python，请确保Python已安装并添加到PATH环境变量中
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python
    )
)

REM 创建logs目录（如果不存在）
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    echo [信息] 已创建日志目录: %LOG_DIR%
)

REM 检查是否已经在运行（通过端口8801）
netstat -ano | findstr ":8801" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [警告] 检测到端口8801已被占用，服务可能已在运行
    echo 请先运行 stop.bat 停止服务，或检查是否有其他程序占用该端口
    pause
    exit /b 1
)

REM 生成日志文件名（使用日期时间）
set "LOG_FILE=%LOG_DIR%\app_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOG_FILE=%LOG_FILE: =0%"

REM 输出启动信息
echo ========================================
echo 启动 Sign Server 服务
echo 项目目录: %PROJECT_DIR%
echo Python命令: %PYTHON_CMD%
echo 日志文件: %LOG_FILE%
echo 端口: 8801
echo ========================================
echo.

REM 先测试Python命令和app.py是否存在
echo 正在检查Python和app.py文件...
if not exist "app.py" (
    echo [错误] 找不到 app.py 文件！
    echo 当前目录: %PROJECT_DIR%
    pause
    exit /b 1
)

"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python命令执行失败: %PYTHON_CMD%
    pause
    exit /b 1
)

REM 创建临时批处理文件来运行Python并重定向日志
set TEMP_RUNNER=%TEMP%\sign_server_%RANDOM%.bat
(
    echo @echo off
    echo cd /d %PROJECT_DIR%
    echo color 0A
    echo echo.
    echo echo  ╔════════════════════════════════════════════════════════════╗
    echo echo  ║                                                            ║
    echo echo  ║          ■■■ 跨境签名程序服务 ■■■                        ║
    echo echo  ║                                                            ║
    echo echo  ╠════════════════════════════════════════════════════════════╣
    echo echo  ║                                                            ║
    echo echo  ║  项目目录: %PROJECT_DIR%
    echo echo  ║                                                            ║
    echo echo  ║  Python命令: %PYTHON_CMD%
    echo echo  ║                                                            ║
    echo echo  ║  日志文件: %LOG_FILE%
    echo echo  ║                                                            ║
    echo echo  ╠════════════════════════════════════════════════════════════╣
    echo echo  ║                                                            ║
    echo echo  ║  ⚠️  警告：请勿关闭此窗口！                               ║
    echo echo  ║                                                            ║
    echo echo  ║  关闭此窗口将导致服务停止！                               ║
    echo echo  ║                                                            ║
    echo echo  ║  如需停止服务，请运行 stop.bat                            ║
    echo echo  ║                                                            ║
    echo echo  ╠════════════════════════════════════════════════════════════╣
    echo echo  ║                                                            ║
    echo echo  ║  服务已启动，正在运行...                                  ║
    echo echo  ║                                                            ║
    echo echo  ╚════════════════════════════════════════════════════════════╝
    echo echo.
    echo "%PYTHON_CMD%" app.py ^>^> "%LOG_FILE%" 2^>^&1
    echo echo.
    echo color 0C
    echo echo  ╔════════════════════════════════════════════════════════════╗
    echo echo  ║                                                            ║
    echo echo  ║  ❌ 程序已退出，退出代码: %%ERRORLEVEL%%                  ║
    echo echo  ║                                                            ║
    echo echo  ║  请查看日志文件获取详细信息:                              ║
    echo echo  ║  %LOG_FILE%
    echo echo  ║                                                            ║
    echo echo  ╚════════════════════════════════════════════════════════════╝
    echo echo.
    echo pause
) > "%TEMP_RUNNER%"

REM 启动服务（使用/k保持窗口打开，显示错误信息）
start "跨境签名程序请勿关闭" cmd /k "%TEMP_RUNNER%"


REM 等待3秒确保进程启动
timeout /t 3 /nobreak >nul

REM 检查进程是否启动成功
netstat -ano | findstr ":8801" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo.
    echo [错误] 服务启动失败！
    echo 请检查：
    echo   1. 日志文件: %LOG_FILE%
    echo   2. 服务窗口中的错误信息
    echo   3. Python是否正确安装
    echo   4. 依赖是否已安装（pip install -r requirements.txt）
    echo.
    pause
    exit /b 1
) else (
    echo [成功] 服务已启动，正在运行
    echo 日志文件: %LOG_FILE%
    echo 使用 stop.bat 可以停止服务
    echo.
    echo 服务窗口已打开，请勿关闭该窗口
    echo 此窗口可以关闭，服务将继续运行
    echo.
    timeout /t 2 /nobreak >nul
)

endlocal

