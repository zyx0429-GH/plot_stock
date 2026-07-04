"""
volume_breakout.py - 量能突破選股策略

條件:
1. 今日成交量 > 5日均量 × 1.5倍
2. 今日收盤價 > 昨日收盤價 (收漲)
3. 成交量創近期新高 (可選)
"""
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from technical import moving_averages


def volume_breakout(df, volume_multiplier=1.5, ma_period=5, price_rise=True):
    """
    量能突破策略
    
    參數:
        volume_multiplier: 成交量放大倍數 (預設 1.5)
        ma_period: 成交量均線期間 (預設 5)
        price_rise: 是否要求收漲 (預設 True)
    
    回傳: Series (1=符合條件, 0=不符合)
    """
    vol_ma = df['Volume'].rolling(window=ma_period).mean()
    
    condition = df['Volume'] > vol_ma * volume_multiplier
    if price_rise:
        condition = condition & (df['Close'] > df['Close'].shift(1))
    
    return condition.astype(int)


def volume_breakout_screen(df, volume_multiplier=1.5, ma_period=5, price_rise=True):
    """
    量能突破篩選 — 回傳最近一筆是否觸發
    """
    signals = volume_breakout(df, volume_multiplier, ma_period, price_rise)
    return bool(signals.iloc[-1]) if len(signals) > 0 else False


def volume_breakout_info(df, volume_multiplier=1.5, ma_period=5):
    """
    量能突破詳細資訊
    """
    vol_ma = df['Volume'].rolling(window=ma_period).mean()
    latest_vol = df['Volume'].iloc[-1]
    latest_vol_ma = vol_ma.iloc[-1]
    latest_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else latest_close
    
    ratio = latest_vol / latest_vol_ma if latest_vol_ma > 0 else 0
    is_breakout = (latest_vol > latest_vol_ma * volume_multiplier) and (latest_close > prev_close)
    
    return {
        'volume': int(latest_vol),
        'volume_ma': int(latest_vol_ma),
        'ratio': round(ratio, 2),
        'is_breakout': is_breakout,
        'signal': '量能突破' if is_breakout else '無訊號'
    }
