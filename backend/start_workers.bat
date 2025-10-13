@echo off
REM Start hybrid queue workers using conda Python

echo Starting hybrid queue workers...
echo.

REM Activate conda base environment and run
call conda activate base
if errorlevel 1 (
    echo Failed to activate conda environment
    exit /b 1
)

echo Using Python:
python --version
python -c "import sys; print(sys.executable)"
echo.

echo Starting workers...
python start_hybrid_queue.py

pause
