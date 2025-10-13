# Start hybrid queue workers using conda Python

Write-Host "Starting hybrid queue workers..." -ForegroundColor Green
Write-Host ""

# Get conda path
$condaPath = (Get-Command conda -ErrorAction SilentlyContinue).Source
if (-not $condaPath) {
    Write-Host "Error: Conda not found in PATH" -ForegroundColor Red
    exit 1
}

# Activate conda base environment
Write-Host "Activating conda base environment..." -ForegroundColor Yellow
& conda activate base

# Show Python being used
Write-Host "Using Python:" -ForegroundColor Cyan
& python --version
& python -c "import sys; print(sys.executable)"
Write-Host ""

# Check if aio-pika is installed
Write-Host "Checking aio-pika installation..." -ForegroundColor Cyan
$aiopikaCheck = & python -c "import aio_pika; print('aio-pika is installed')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: aio-pika is not installed" -ForegroundColor Red
    Write-Host "Install it with: conda install -c conda-forge aio-pika" -ForegroundColor Yellow
    exit 1
}
Write-Host $aiopikaCheck -ForegroundColor Green
Write-Host ""

# Start workers
Write-Host "Starting hybrid queue workers..." -ForegroundColor Green
& python start_hybrid_queue.py
