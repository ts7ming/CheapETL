echo.
echo [提示] 正在启动服务...
echo [提示] 服务地址: http://localhost:5000
echo [提示] 按 Ctrl+C 停止服务
echo.
cd web

start "" "index.html"
start /B pythonw app.py
pause