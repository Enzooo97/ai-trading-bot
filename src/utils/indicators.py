"""
Technical indicator wrapper using manual calculations.
Provides compatibility across all Python versions without external TA libraries.
"""
import pandas as pd
import numpy as np

# Use manual calculations (no external dependencies needed)
USE_PANDAS_TA = False


def sma(series: pd.Series, length: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=length).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD indicator."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({
        f'MACD_{fast}_{slow}_{signal}': macd_line,
        f'MACDs_{fast}_{slow}_{signal}': signal_line,
        f'MACDh_{fast}_{slow}_{signal}': hist,
    }, index=series.index)


def bbands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands."""
    middle = series.rolling(window=length).mean()
    std_dev = series.rolling(window=length).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return pd.DataFrame({
        f'BBU_{length}_{std}': upper,
        f'BBM_{length}_{std}': middle,
        f'BBL_{length}_{std}': lower,
    }, index=series.index)


def stoch(high: pd.Series, low: pd.Series, close: pd.Series,
          k: int = 14, d: int = 3, smooth_k: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator."""
    lowest_low = low.rolling(window=k).min()
    highest_high = high.rolling(window=k).max()
    fastk = 100 * (close - lowest_low) / (highest_high - lowest_low)
    slowk = fastk.rolling(window=smooth_k).mean()
    slowd = slowk.rolling(window=d).mean()
    return pd.DataFrame({
        f'STOCHk_{k}_{d}_{smooth_k}': slowk,
        f'STOCHd_{k}_{d}_{smooth_k}': slowd,
    }, index=close.index)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Average True Range."""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=length).mean()


def roc(series: pd.Series, length: int = 10) -> pd.Series:
    """Rate of Change."""
    return ((series - series.shift(length)) / series.shift(length)) * 100


def adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.DataFrame:
    """ADX (Average Directional Index)."""
    # Calculate True Range
    tr = atr(high, low, close, length=1)

    # Calculate Directional Movement
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0)
    minus_dm = down.where((down > up) & (down > 0), 0)

    # Smooth the values
    tr_smooth = tr.rolling(window=length).mean()
    plus_dm_smooth = plus_dm.rolling(window=length).mean()
    minus_dm_smooth = minus_dm.rolling(window=length).mean()

    # Calculate DI+ and DI-
    plus_di = 100 * plus_dm_smooth / tr_smooth
    minus_di = 100 * minus_dm_smooth / tr_smooth

    # Calculate DX and ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_val = dx.rolling(window=length).mean()

    return pd.DataFrame({
        f'ADX_{length}': adx_val,
        f'DMP_{length}': plus_di,
        f'DMN_{length}': minus_di,
    }, index=close.index)
