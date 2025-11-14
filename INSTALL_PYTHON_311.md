# Installing Python 3.11 and Setting Up Virtual Environment

## Why Python 3.11?

Python 3.11 has the best compatibility with all our trading bot dependencies:
- ✅ pandas-ta (requires Python <3.14)
- ✅ numba (requires Python <3.14)
- ✅ vectorbt (optional, requires Python <3.14)
- ✅ All other packages work perfectly
- ✅ Stable and well-tested

## Step 1: Install Python 3.11

### Option A: Download from Python.org (Recommended)

1. Visit: https://www.python.org/downloads/release/python-3119/
2. Scroll down to "Files"
3. Download: **Windows installer (64-bit)**
   - Direct link: `python-3.11.9-amd64.exe`
4. Run installer:
   - ✅ Check "Add Python 3.11 to PATH"
   - ✅ Check "Install for all users"
   - Click "Install Now"

### Option B: Using Chocolatey (Windows Package Manager)

```powershell
# If you have Chocolatey installed
choco install python --version=3.11.9
```

### Option C: Using winget (Windows 11)

```powershell
winget install Python.Python.3.11
```

### Verify Installation

```powershell
# Check Python 3.11 is installed
python --version
# Should show: Python 3.11.x

# Or specifically call Python 3.11
py -3.11 --version
```

## Step 2: Create Virtual Environment

Once Python 3.11 is installed:

### Navigate to Project Directory

```powershell
cd "C:\Users\cerre\VSC_PROJ\Trading Programes\Trading_Bot_ModerateScalping_Mk1"
```

### Create Virtual Environment

```powershell
# Using Python 3.11 explicitly
py -3.11 -m venv venv

# Or if Python 3.11 is default:
python -m venv venv
```

This creates a `venv` folder with Python 3.11.

### Activate Virtual Environment

```powershell
# Activate the virtual environment
.\venv\Scripts\activate

# You should see (venv) at the start of your prompt
```

### Verify Virtual Environment

```powershell
# Check Python version in venv
python --version
# Should show: Python 3.11.x

# Check pip
pip --version
# Should show pip with Python 3.11
```

## Step 3: Install All Dependencies

With the virtual environment activated:

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

This will now install:
- ✅ pandas-ta (will work now!)
- ✅ numba (will work now!)
- ✅ All other packages

## Step 4: Verify Installation

```powershell
# Test imports
python -c "import pandas_ta; print('pandas-ta:', pandas_ta.__version__)"
python -c "import numba; print('numba:', numba.__version__)"
python -c "import talib; print('TA-Lib:', talib.__version__)"
python -c "from src.strategies import VWAPStrategy; print('Strategies: OK')"
```

## Step 5: Update .env File

```powershell
# .env file should already exist
# Add your Alpaca API keys:
notepad .env
```

Replace:
```
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
```

With your actual keys from alpaca.markets

## Step 6: Run First Backtest

```powershell
# With venv activated
python run_backtest.py --strategy all --symbols AAPL MSFT GOOGL --days 30
```

## Troubleshooting

### "py -3.11" not found

If `py -3.11` doesn't work:

1. Find Python 3.11 installation path:
   ```powershell
   where python
   ```

2. Use full path:
   ```powershell
   C:\Python311\python.exe -m venv venv
   ```

### Multiple Python Versions

If you have multiple Python versions:

1. Use Python Launcher:
   ```powershell
   py -0  # List all Python versions
   py -3.11 -m venv venv  # Use specific version
   ```

2. Or uninstall Python 3.14 and keep only 3.11

### Virtual Environment Not Activating

```powershell
# If activation fails, try:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again:
.\venv\Scripts\activate
```

### TA-Lib Installation Issues (Optional)

If TA-Lib binary fails to install:

1. Download pre-built wheel:
   - Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   - Download: `TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl`

2. Install wheel:
   ```powershell
   pip install TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl
   ```

3. Or use our indicator wrapper (already created):
   - Works with either pandas-ta or TA-Lib
   - Falls back automatically

## Daily Usage

### Always Activate Virtual Environment First

```powershell
# Navigate to project
cd "C:\Users\cerre\VSC_PROJ\Trading Programes\Trading_Bot_ModerateScalping_Mk1"

# Activate venv
.\venv\Scripts\activate

# Now run commands
python run_backtest.py --strategy all --days 30
python main.py
```

### Deactivate When Done

```powershell
deactivate
```

## VS Code Integration

If using VS Code:

1. Open project folder in VS Code
2. Press `Ctrl+Shift+P`
3. Type: "Python: Select Interpreter"
4. Choose: `.\venv\Scripts\python.exe`
5. VS Code will now use your virtual environment automatically

## Quick Setup Script

Create `setup_venv.ps1`:

```powershell
# setup_venv.ps1
Write-Host "Setting up Python 3.11 virtual environment..." -ForegroundColor Green

# Create venv
py -3.11 -m venv venv

# Activate
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

Write-Host "Setup complete! Virtual environment ready." -ForegroundColor Green
Write-Host "To activate: .\venv\Scripts\activate" -ForegroundColor Yellow
```

Run it:
```powershell
.\setup_venv.ps1
```

## Benefits of Virtual Environment

✅ **Isolated Dependencies**: No conflicts with other Python projects
✅ **Reproducible**: Same packages across different machines
✅ **Clean**: Easy to delete and recreate if needed
✅ **Version Control**: Can use different Python versions per project

## Next Steps After Setup

1. ✅ Python 3.11 installed
2. ✅ Virtual environment created
3. ✅ Dependencies installed
4. ✅ .env configured with API keys
5. ✅ Ready to backtest!

Run:
```powershell
python run_backtest.py --strategy all --days 30
```

---

**Need Help?**
- Python 3.11 download: https://www.python.org/downloads/release/python-3119/
- Virtual environments: https://docs.python.org/3/tutorial/venv.html
- Alpaca API keys: https://alpaca.markets/docs/trading/getting-started/
