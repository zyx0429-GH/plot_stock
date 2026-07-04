"""
macd.py - MACD 指標
"""
import pandas as pd
import numpy as np


def macd(df, fast=12, slow=26, signal=9, column='Close'):
    """
    計算 MACD 指標
    回傳 DataFrame 含 ['DIF', 'DEA', 'MACD_Hist']
    """
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = dif - dea
    
    result = pd.DataFrame({
        'DIF': dif,
        'DEA': dea,
        'MACD_Hist': hist
    }, index=df.index)
    return result


def macd_signal(df, fast=12, slow=26, signal=9, column='Close'):
    """
    MACD 訊號
    回傳: 1=黃金交叉(DIF上穿DEA), -1=死亡交叉(DIF下穿DEA), 0=無訊號
    """
    macd_df = macd(df, fast, slow, signal, column)
    dif = macd_df['DIF']
    dea = macd_df['DEA']
    
    signal_series = pd.Series(0, index=df.index)
    signal_series[(dif.shift(1) <= dea.shift(1)) & (dif > dea)] = 1
    signal_series[(dif.shift(1) >= dea.shift(1)) & (dif < dea)] = -1
    return signal_series


def macd_score(df, fast=12, slow=26, signal=9, column='Close'):
    """
    MACD 綜合評分 (0-100)
    基於: DIF位置、柱狀體方向、交叉訊號
    """
    macd_df = macd(df, fast, slow, signal, column)
    dif = macd_df['DIF'].iloc[-1]
    hist = macd_df['MACD_Hist'].iloc[-1]
    
    if pd.isna(dif) or pd.isna(hist):
        return 50
    
    score = 50
    # DIF > 0 加分
    if dif > 0:
        score += 15
    else:
        score -= 15
    
    # 柱狀體為正加分
    if hist > 0:
        score += 15
    else:
        score -= 15
    
    # 柱狀體擴大加分
    if len(macd_df) >= 2:
        prev_hist = macd_df['MACD_Hist'].iloc[-2]
        if hist > prev_hist:
            score += 10
        else:
            score -= 10
    
    return max(0, min(100, score))


def macd_summary(df, fast=12, slow=26, signal=9, column='Close'):
    """
    MACD 綜合摘要
    回傳 dict 含最新數值與訊號
    """
    macd_df = macd(df, fast, slow, signal, column)
    latest = macd_df.iloc[-1]
    
    dif = latest['DIF']
    dea = latest['DEA']
    hist = latest['MACD_Hist']
    
    # 訊號判斷
    if pd.isna(dif) or pd.isna(dea):
        signal_text = '資料不足'
    elif dif > dea and dif > 0:
        signal_text = '多頭強勢'
    elif dif > dea and dif < 0:
        signal_text = '多頭轉強'
    elif dif < dea and dif > 0:
        signal_text = '多頭轉弱'
    else:
        signal_text = '空頭弱勢'
    
    return {
        'dif': round(dif, 4) if not pd.isna(dif) else '-',
        'dea': round(dea, 4) if not pd.isna(dea) else '-',
        'hist': round(hist, 4) if not pd.isna(hist) else '-',
        'score': macd_score(df, fast, slow, signal, column),
        'signal': signal_text,
    }
