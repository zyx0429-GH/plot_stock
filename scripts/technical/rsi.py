"""
rsi.py - 相對強弱指標 (RSI)
"""
import pandas as pd
import numpy as np


def rsi(df, period=14, column='Close'):
    """
    計算 RSI 相對強弱指標
    回傳 Series (0-100)
    """
    delta = df[column].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val


def rsi_signal(df, period=14, column='Close', overbought=70, oversold=30):
    """
    RSI 訊號
    回傳: 1=超賣(買入訊號), -1=超買(賣出訊號), 0=無訊號
    """
    rsi_val = rsi(df, period, column)
    signal = pd.Series(0, index=df.index)
    signal[rsi_val < oversold] = 1
    signal[rsi_val > overbought] = -1
    return signal


def rsi_divergence(df, period=14, column='Close'):
    """
    RSI 背離偵測
    回傳: 'bullish_divergence', 'bearish_divergence', 'none'
    """
    rsi_val = rsi(df, period, column)
    price = df[column]
    
    # 找最近兩個低點 / 高點
    if len(price) < 10:
        return 'none'
    
    # 簡化：比較最近5天和再前5天
    recent_low_price = price.iloc[-5:].min()
    recent_low_rsi = rsi_val.iloc[-5:].min()
    prev_low_price = price.iloc[-10:-5].min()
    prev_low_rsi = rsi_val.iloc[-10:-5].min()
    
    if recent_low_price < prev_low_price and recent_low_rsi > prev_low_rsi:
        return 'bullish_divergence'
    
    recent_high_price = price.iloc[-5:].max()
    recent_high_rsi = rsi_val.iloc[-5:].max()
    prev_high_price = price.iloc[-10:-5].max()
    prev_high_rsi = rsi_val.iloc[-10:-5].max()
    
    if recent_high_price > prev_high_price and recent_high_rsi < prev_high_rsi:
        return 'bearish_divergence'
    
    return 'none'
