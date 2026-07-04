"""
bollinger_bands.py - 布林通道 (Bollinger Bands)
"""
import pandas as pd
import numpy as np


def bollinger_bands(df, period=20, std_dev=2, column='Close'):
    """
    計算布林通道
    回傳 DataFrame 含 ['Middle', 'Upper', 'Lower', 'Bandwidth', '%B']
    """
    middle = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    # 帶寬 (Bandwidth)
    bandwidth = ((upper - lower) / middle) * 100
    
    # %B 指標
    bb_pct = (df[column] - lower) / (upper - lower)
    
    result = pd.DataFrame({
        'Middle': middle,
        'Upper': upper,
        'Lower': lower,
        'Bandwidth': bandwidth,
        'PctB': bb_pct
    }, index=df.index)
    return result


def bollinger_position(df, period=20, std_dev=2, column='Close'):
    """
    判斷股價在布林通道的位置
    回傳: 'upper_band', 'upper_half', 'middle', 'lower_half', 'lower_band'
    """
    bb = bollinger_bands(df, period, std_dev, column)
    latest_close = df[column].iloc[-1]
    upper = bb['Upper'].iloc[-1]
    lower = bb['Lower'].iloc[-1]
    middle = bb['Middle'].iloc[-1]
    
    if pd.isna(upper) or pd.isna(lower):
        return 'unknown'
    
    if latest_close >= upper:
        return 'upper_band'
    elif latest_close <= lower:
        return 'lower_band'
    elif latest_close > middle:
        return 'upper_half'
    elif latest_close < middle:
        return 'lower_half'
    return 'middle'


def bollinger_signal(df, period=20, std_dev=2, column='Close'):
    """
    布林通道訊號
    回傳: Series (1=觸及下軌(買入), -1=觸及上軌(賣出), 0=無訊號)
    """
    bb = bollinger_bands(df, period, std_dev, column)
    close = df[column]
    upper = bb['Upper']
    lower = bb['Lower']
    
    signal = pd.Series(0, index=df.index)
    signal[close >= upper] = -1
    signal[close <= lower] = 1
    return signal


def bollinger_squeeze(df, period=20, std_dev=2, column='Close', lookback=20):
    """
    偵測布林通道收斂 (Squeeze)
    帶寬創近期新低時視為即將突破
    回傳: True/False
    """
    bb = bollinger_bands(df, period, std_dev, column)
    bandwidth = bb['Bandwidth']
    
    if len(bandwidth) < lookback + period:
        return False
    
    current_bw = bandwidth.iloc[-1]
    min_bw = bandwidth.iloc[-lookback:-1].min()
    
    if pd.isna(current_bw) or pd.isna(min_bw):
        return False
    
    return current_bw < min_bw * 0.95


def bollinger_summary(df, period=20, std_dev=2, column='Close'):
    """
    布林通道綜合摘要
    """
    bb = bollinger_bands(df, period, std_dev, column)
    latest = bb.iloc[-1]
    position = bollinger_position(df, period, std_dev, column)
    squeeze = bollinger_squeeze(df, period, std_dev, column)
    
    pos_text = {
        'upper_band': '觸及上軌',
        'upper_half': '上軌與中軌之間',
        'middle': '中軌附近',
        'lower_half': '下軌與中軌之間',
        'lower_band': '觸及下軌',
        'unknown': '未知'
    }
    
    return {
        'upper': round(latest['Upper'], 2) if not pd.isna(latest['Upper']) else '-',
        'middle': round(latest['Middle'], 2) if not pd.isna(latest['Middle']) else '-',
        'lower': round(latest['Lower'], 2) if not pd.isna(latest['Lower']) else '-',
        'bandwidth': round(latest['Bandwidth'], 2) if not pd.isna(latest['Bandwidth']) else '-',
        'pct_b': round(latest['PctB'], 4) if not pd.isna(latest['PctB']) else '-',
        'position': position,
        'position_text': pos_text.get(position, '未知'),
        'squeeze': squeeze,
    }
