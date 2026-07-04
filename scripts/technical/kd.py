"""
kd.py - KD 隨機指標 (Stochastic Oscillator)
"""
import pandas as pd
import numpy as np


def kd(df, n=9, m1=3, m2=3):
    """
    計算 KD 隨機指標
    參數:
        n: RSV 計算期間 (預設9)
        m1: K 值平滑天數 (預設3)
        m2: D 值平滑天數 (預設3)
    回傳 DataFrame 含 ['K', 'D', 'RSV']
    """
    low_min = df['Low'].rolling(window=n, min_periods=1).min()
    high_max = df['High'].rolling(window=n, min_periods=1).max()
    
    # RSV
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)
    
    # K 值 (初始值設為50)
    k = pd.Series(index=df.index, dtype=float)
    k.iloc[0] = 50
    for i in range(1, len(df)):
        k.iloc[i] = (2/3) * k.iloc[i-1] + (1/3) * rsv.iloc[i]
    
    # D 值 (初始值設為50)
    d = pd.Series(index=df.index, dtype=float)
    d.iloc[0] = 50
    for i in range(1, len(df)):
        d.iloc[i] = (2/3) * d.iloc[i-1] + (1/3) * k.iloc[i]
    
    result = pd.DataFrame({
        'K': k,
        'D': d,
        'RSV': rsv
    }, index=df.index)
    return result


def kd_signal(df, n=9, m1=3, m2=3, overbought=80, oversold=20):
    """
    KD 訊號
    回傳: 1=K上穿D且超賣區(黃金交叉), -1=K下穿D且超買區(死亡交叉), 0=無訊號
    """
    kd_df = kd(df, n, m1, m2)
    k = kd_df['K']
    d = kd_df['D']
    
    signal = pd.Series(0, index=df.index)
    
    # 黃金交叉: K 上穿 D 且在超賣區附近
    golden = (k.shift(1) <= d.shift(1)) & (k > d) & (d < overbought)
    # 死亡交叉: K 下穿 D 且在超買區附近
    death = (k.shift(1) >= d.shift(1)) & (k < d) & (d > oversold)
    
    signal[golden] = 1
    signal[death] = -1
    return signal


def kd_summary(df, n=9, m1=3, m2=3):
    """
    KD 綜合摘要
    回傳 dict 含最新 K, D 值與訊號
    """
    kd_df = kd(df, n, m1, m2)
    latest = kd_df.iloc[-1]
    
    k_val = latest['K']
    d_val = latest['D']
    
    if pd.isna(k_val) or pd.isna(d_val):
        return {'k': '-', 'd': '-', 'signal': '資料不足'}
    
    # 訊號判斷
    if k_val > 80 and d_val > 80:
        signal_text = '超買區 — 注意回檔'
    elif k_val < 20 and d_val < 20:
        signal_text = '超賣區 — 可能反彈'
    elif k_val > d_val and k_val > d_val + 5:
        signal_text = '黃金交叉 — 偏多'
    elif k_val < d_val and d_val > k_val + 5:
        signal_text = '死亡交叉 — 偏空'
    else:
        signal_text = '盤整 — 方向不明'
    
    return {
        'k': round(k_val, 2),
        'd': round(d_val, 2),
        'rsv': round(latest['RSV'], 2) if not pd.isna(latest['RSV']) else '-',
        'signal': signal_text,
    }
