@echo off
chcp 65001 >nul
cd /d "%~dp0"

where pythonw >nul 2>nul
if errorlevel 1 (
    echo 没找到 Python。请先安装 Python 3.10+，安装时勾选 "Add python.exe to PATH"。
    pause
    exit /b 1
)

python -c "import PIL" >nul 2>nul
if errorlevel 1 (
    echo 正在安装 Pillow...
    python -m pip install pillow
    if errorlevel 1 (
        echo Pillow 安装失败，请手动运行：python -m pip install pillow
        pause
        exit /b 1
    )
)

start "" pythonw skin_head_gui.py
