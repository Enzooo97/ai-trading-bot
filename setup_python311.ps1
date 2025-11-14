# Automated Python 3.11 Setup Script for Trading Bot
# Run this script to set up Python 3.11 virtual environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Trading Bot - Python 3.11 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.11 is installed
Write-Host "Checking for Python 3.11..." -ForegroundColor Yellow
$python311Path = $null

try {
    # Try py launcher first
    $pyVersion = & py -3.11 --version 2>&1
    if ($pyVersion -match "Python 3.11") {
        $python311Path = "py -3.11"
        Write-Host "✓ Found Python 3.11 via py launcher" -ForegroundColor Green
    }
} catch {}

if (-not $python311Path) {
    # Try direct python command
    try {
        $pyVersion = & python --version 2>&1
        if ($pyVersion -match "Python 3.11") {
            $python311Path = "python"
            Write-Host "✓ Found Python 3.11 as default" -ForegroundColor Green
        }
    } catch {}
}

if (-not $python311Path) {
    Write-Host "✗ Python 3.11 not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.11 first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.python.org/downloads/release/python-3119/" -ForegroundColor White
    Write-Host "2. Run installer and check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Re-run this script" -ForegroundColor White
    Write-Host ""

    # Ask if user wants to open download page
    $response = Read-Host "Open download page now? (y/n)"
    if ($response -eq 'y') {
        Start-Process "https://www.python.org/downloads/release/python-3119/"
    }

    exit 1
}

Write-Host ""

# Check if venv already exists
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
    $response = Read-Host "Delete and recreate? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Removing old virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "Using existing virtual environment." -ForegroundColor Green
        Write-Host ""
        Write-Host "To activate: .\venv\Scripts\activate" -ForegroundColor Cyan
        exit 0
    }
}

# Create virtual environment
Write-Host "Creating Python 3.11 virtual environment..." -ForegroundColor Yellow

if ($python311Path -eq "py -3.11") {
    & py -3.11 -m venv venv
} else {
    & python -m venv venv
}

if (-not $?) {
    Write-Host "✗ Failed to create virtual environment!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Virtual environment created" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

if (-not $?) {
    Write-Host "✗ Failed to activate virtual environment!" -ForegroundColor Red
    Write-Host "You may need to enable script execution:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
    exit 1
}

Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Verify Python version
Write-Host "Verifying Python version..." -ForegroundColor Yellow
$venvPython = & python --version
Write-Host "  $venvPython" -ForegroundColor White

if ($venvPython -notmatch "Python 3.11") {
    Write-Host "✗ Warning: Virtual environment is not using Python 3.11!" -ForegroundColor Red
}

Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& python -m pip install --upgrade pip --quiet

if ($?) {
    Write-Host "✓ Pip upgraded" -ForegroundColor Green
} else {
    Write-Host "✗ Pip upgrade failed (continuing anyway)" -ForegroundColor Yellow
}

Write-Host ""

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes...)" -ForegroundColor Gray
Write-Host ""

& pip install -r requirements.txt

if ($?) {
    Write-Host ""
    Write-Host "✓ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Some dependencies may have failed to install" -ForegroundColor Yellow
    Write-Host "Check the output above for errors" -ForegroundColor Yellow
}

Write-Host ""

# Test imports
Write-Host "Testing key imports..." -ForegroundColor Yellow

$tests = @(
    @("pandas", "import pandas"),
    @("numpy", "import numpy"),
    @("alpaca-py", "import alpaca"),
    @("TA-Lib", "import talib"),
    @("pandas-ta", "import pandas_ta"),
    @("strategies", "from src.strategies import VWAPStrategy")
)

$allPassed = $true

foreach ($test in $tests) {
    $name = $test[0]
    $import = $test[1]

    try {
        & python -c $import 2>$null
        if ($?) {
            Write-Host "  ✓ $name" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $name" -ForegroundColor Red
            $allPassed = $false
        }
    } catch {
        Write-Host "  ✗ $name" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""

if ($allPassed) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "⚠ Setup Complete (with warnings)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Add your Alpaca API keys to .env file" -ForegroundColor White
Write-Host "   Edit: .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run your first backtest:" -ForegroundColor White
Write-Host "   python run_backtest.py --strategy all --days 30" -ForegroundColor Gray
Write-Host ""
Write-Host "To activate venv in future:" -ForegroundColor Cyan
Write-Host "   .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host ""
Write-Host "To deactivate venv:" -ForegroundColor Cyan
Write-Host "   deactivate" -ForegroundColor Gray
Write-Host ""

# Pause so user can read
Write-Host "Press any key to continue..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
