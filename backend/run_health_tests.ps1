#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive System Health Test Runner for CodeNova

.DESCRIPTION
    This PowerShell script provides easy access to the system health testing script
    with various options for different types of tests.

.PARAMETER ConfigOnly
    Only test configuration validation

.PARAMETER SpacesOnly
    Only test Digital Ocean Spaces

.PARAMETER GitHubOnly
    Only test GitHub integration

.PARAMETER QueueOnly
    Only test job queue system

.PARAMETER Performance
    Include performance tests

.PARAMETER Verbose
    Enable verbose output

.PARAMETER Json
    Output results in JSON format

.PARAMETER Help
    Show help information

.EXAMPLE
    .\run_health_tests.ps1
    Run all health tests

.EXAMPLE
    .\run_health_tests.ps1 -ConfigOnly -Verbose
    Test configuration only with verbose output

.EXAMPLE
    .\run_health_tests.ps1 -SpacesOnly -Json
    Test Digital Ocean Spaces only and output in JSON format

#>

param(
    [switch]$ConfigOnly,
    [switch]$SpacesOnly,
    [switch]$GitHubOnly,
    [switch]$QueueOnly,
    [switch]$Performance,
    [switch]$Verbose,
    [switch]$Json,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

Write-Host "CodeNova System Health Test Runner" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Using Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again." -ForegroundColor Red
    exit 1
}

# Build arguments array
$args = @()
$testType = "comprehensive"

if ($ConfigOnly) {
    $args += "--config-only"
    $testType = "configuration"
}
if ($SpacesOnly) {
    $args += "--spaces-only"
    $testType = "Digital Ocean Spaces"
}
if ($GitHubOnly) {
    $args += "--github-only"
    $testType = "GitHub integration"
}
if ($QueueOnly) {
    $args += "--queue-only"
    $testType = "job queue system"
}
if ($Performance) {
    $args += "--performance"
}
if ($Verbose) {
    $args += "--verbose"
}
if ($Json) {
    $args += "--json"
}

Write-Host "Running $testType health tests..." -ForegroundColor Yellow
Write-Host ""

# Run the Python test script
try {
    $process = Start-Process -FilePath "python" -ArgumentList (@("test_system_health.py") + $args) -Wait -PassThru -NoNewWindow
    $exitCode = $process.ExitCode
} catch {
    Write-Host "ERROR: Failed to run health tests: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Interpret exit code
switch ($exitCode) {
    0 {
        Write-Host "✓ All tests passed successfully" -ForegroundColor Green
    }
    1 {
        Write-Host "✗ Some tests failed - check the output above" -ForegroundColor Red
    }
    2 {
        Write-Host "⚠ Tests completed with warnings - check the output above" -ForegroundColor Yellow
    }
    default {
        Write-Host "? Unexpected exit code: $exitCode" -ForegroundColor Magenta
    }
}

Write-Host ""
Write-Host "Test completed with exit code: $exitCode" -ForegroundColor Cyan

exit $exitCode