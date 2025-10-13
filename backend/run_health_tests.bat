@echo off
REM Comprehensive System Health Test Runner for Windows
REM
REM This batch file provides easy access to the system health testing script
REM with various options for different types of tests.

echo CodeNova System Health Test Runner
echo ===================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Parse command line arguments
set "ARGS="
set "TEST_TYPE=comprehensive"

:parse_args
if "%1"=="" goto run_test
if "%1"=="--config" (
    set "ARGS=%ARGS% --config-only"
    set "TEST_TYPE=configuration"
    shift
    goto parse_args
)
if "%1"=="--spaces" (
    set "ARGS=%ARGS% --spaces-only"
    set "TEST_TYPE=spaces"
    shift
    goto parse_args
)
if "%1"=="--github" (
    set "ARGS=%ARGS% --github-only"
    set "TEST_TYPE=github"
    shift
    goto parse_args
)
if "%1"=="--queue" (
    set "ARGS=%ARGS% --queue-only"
    set "TEST_TYPE=queue"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "ARGS=%ARGS% --verbose"
    shift
    goto parse_args
)
if "%1"=="--json" (
    set "ARGS=%ARGS% --json"
    shift
    goto parse_args
)
if "%1"=="--performance" (
    set "ARGS=%ARGS% --performance"
    shift
    goto parse_args
)
if "%1"=="--help" (
    goto show_help
)
REM Unknown argument, pass it through
set "ARGS=%ARGS% %1"
shift
goto parse_args

:show_help
echo.
echo Usage: run_health_tests.bat [options]
echo.
echo Options:
echo   --config      Only test configuration validation
echo   --spaces      Only test Digital Ocean Spaces
echo   --github      Only test GitHub integration
echo   --queue       Only test job queue system
echo   --performance Include performance tests
echo   --verbose     Enable verbose output
echo   --json        Output results in JSON format
echo   --help        Show this help message
echo.
echo Examples:
echo   run_health_tests.bat                    # Run all tests
echo   run_health_tests.bat --config          # Test configuration only
echo   run_health_tests.bat --spaces --verbose # Test Spaces with verbose output
echo   run_health_tests.bat --json            # Output in JSON format
echo.
pause
exit /b 0

:run_test
echo Running %TEST_TYPE% health tests...
echo.

REM Run the Python test script
python test_system_health.py %ARGS%

REM Capture exit code
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE%==0 (
    echo ✓ All tests passed successfully
) else if %EXIT_CODE%==1 (
    echo ✗ Some tests failed - check the output above
) else if %EXIT_CODE%==2 (
    echo ⚠ Tests completed with warnings - check the output above
) else (
    echo ? Unexpected exit code: %EXIT_CODE%
)

echo.
echo Test completed with exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%