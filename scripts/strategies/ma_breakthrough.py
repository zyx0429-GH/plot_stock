"""
ma_breakthrough.py - 均線突破選股策略

條件:
1. 收盤價突破短期均線 (例如 MA20)
2. 短期均線 > 長期均線 (多頭排列)
3. 成交量放大 (可選)
"""
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from technical import moving_averages


def ma_breakthrough(df, short=20, long=60, require_volume=False, volume_ma=5):
    """
    均線突破策略
    
    參數:
        short: 短期均線 (預設 20)
        long: 長期均線 (預設 60)
        require_volume: 是否要求放量 (預設 False)
        volume_ma: 成交量均線期間 (預設 5)
    
    回傳: Series (1=符合條件, 0=不符合)
    """
    short_ma = moving_averages.sma(df, short)
    long_ma = moving_averages.sma(df, long)
    
    # 收盤價突破短期均線
    price_break = (df['Close'] > short_ma) & (df['Close'].shift(1) <= short_ma.shift(1))
    
    # 短期均線在長期均線之上
    ma_bull = short_ma > long_ma
    
    condition = price_break & ma_bull
    
    if require_volume:
        vol_ma = df['Volume'].rolling(window=volume_ma).mean()
        condition = condition & (df['Volume'] > vol_ma * 1.2)
    
    return condition.astype(int)


def ma_breakthrough_screen(df, short=20, long=60, require_volume=False):
    """
    均線突破篩選 — 回傳最近一筆是否觸發
    """
    signals = ma_breakthrough(df, short, long, require_volume)
    return bool(signals.iloc[-1]) if len(signals) > 0 else False


def ma_breakthrough_info(df, short=20, long=60):
    """
    均線突破詳細資訊
    """
    short_ma = moving_averages.sma(df, short)
    long_ma = moving_averages.sma(df, long)
    
    latest_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else latest_close
    latest_short = short_ma.iloc[-1]
    latest_long = long_ma.iloc[-1]
    
    is_break = (latest_close > latest_short) and (prev_close <= short_ma.iloc[-2] if len(df) > 1 else False)
    is_bull = latest_short > latest_long if not pd.isna(latest_short) and not pd.isna(latest_long) else False
    
    return {
        'close': round(latest_close, 2),
        'ma_short': round(latest_short, 2) if not pd.isna(latest_short) else '-',
        'ma_long': round(latest_long, 2) if not pd.isna(latest_long) else '-',
        'is_breakthrough': is_break,
        'is_bullish': is_bull,
        'signal': '均線突破' if is_break and is_bull else '多頭排列' if is_bull else '無訊號'
    }
