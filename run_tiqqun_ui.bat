@echo off
setlocal
rem >>> VA: arrenca la UI de TIQQUN i obre el navegador <<<

rem 1) Ves al projecte UI
cd /d "C:\Users\Limits\Desktop\TIQQUN\tiqqun-ui"

rem 2) Assegura Node (ruta “portable” que vas instal·lar)
set "NODE_DIR=C:\Users\Limits\NodePortable\node-v22.20.0-win-x64"
if exist "%NODE_DIR%\node.exe" set "PATH=%NODE_DIR%;%NODE_DIR%\node_modules\npm\bin;%PATH%"

rem 3) (opcional) si no hi ha dependències, instal·la-les
if not exist "node_modules" (
  echo Installing dependencies...
  npm install
)

rem 4) Inicia Vite MINIMITZAT i obre el navegador a la taula
start "TIQQUN Server" /MIN cmd /c "npm run dev"
rem petit delay perquè arrenqui…
timeout /t 2 >nul
start "" "http://localhost:5173"

endlocal
