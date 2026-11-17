$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv }
$pythonExe = Resolve-Path '.venv\Scripts\python.exe'
& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }
& $pythonExe -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all imageio_ffmpeg --name SunoStudio main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
Write-Host "Build complete: dist\SunoStudio.exe"
