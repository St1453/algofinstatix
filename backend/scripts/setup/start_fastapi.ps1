# Start FastAPI application using Poetry and open API documentation

function Find-ProjectRoot {
    param (
        [string]$startDir = $PSScriptRoot
    )
    
    $currentDir = Resolve-Path $startDir
    $root = [System.IO.Path]::GetPathRoot($currentDir)
    
    while ($currentDir -ne $root) {
        $pyprojectPath = Join-Path $currentDir "pyproject.toml"
        if (Test-Path $pyprojectPath) {
            return $currentDir
        }
        $parent = Split-Path $currentDir -Parent
        if ($parent -eq $currentDir) { break }
        $currentDir = $parent
    }
    
    return $null
}

# Find the project root
$projectRoot = Find-ProjectRoot -startDir $PSScriptRoot

if (-not $projectRoot) {
    Write-Error "Error: Could not find pyproject.toml in any parent directory"
    exit 1
}

Write-Host "Found project root: $projectRoot" -ForegroundColor Green
Set-Location -Path $projectRoot

# Check if Poetry is installed
$poetryCheck = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryCheck) {
    Write-Error "Poetry is not installed. Please install Poetry first: https://python-poetry.org/docs/#installation"
    exit 1
}

# Install dependencies if not already installed
Write-Host "Installing dependencies with Poetry..." -ForegroundColor Cyan
poetry install --no-interaction --no-ansi

# Start the FastAPI server using Poetry in the background
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
$process = Start-Process -NoNewWindow -FilePath "poetry" -ArgumentList "run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Wait for the server to start
Start-Sleep -Seconds 3

# Check if the server started successfully
if ($process.HasExited) {
    Write-Error "Failed to start FastAPI server. Check for errors above."
    exit 1
}

# Open the API documentation in the default web browser
$docsUrl = "http://127.0.0.1:8000/docs"
Write-Host "Opening API documentation at: $docsUrl" -ForegroundColor Green
Start-Process $docsUrl

# Display help message
Write-Host "`nFastAPI server is running. Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host "API Documentation: $docsUrl" -ForegroundColor Cyan
Write-Host "API Base URL: http://127.0.0.1:8000" -ForegroundColor Cyan

# Keep the script running until user presses Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Cleanup: Stop the FastAPI server when the script is terminated
    if ($process -and -not $process.HasExited) {
        Write-Host "`nStopping FastAPI server..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force
    }
    Write-Host "FastAPI server stopped." -ForegroundColor Green
}