$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv }
$pythonExe = Resolve-Path '.venv\Scripts\python.exe'
& $pythonExe -m pip install -r requirements.txt
& $pythonExe -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all imageio_ffmpeg --name SunoStudio main.py
Write-Host "Build complete: dist\SunoStudio.exe"
