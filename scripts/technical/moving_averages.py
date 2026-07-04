"""
moving_averages.py - 移動平均線技術指標
提供 SMA, EMA, WMA 計算
"""
import pandas as pd
import numpy as np


def sma(df, period=20, column='Close'):
    """簡單移動平均線 (Simple Moving Average)"""
    return df[column].rolling(window=period, min_periods=1).mean()


def ema(df, period=20, column='Close'):
    """指數移動平均線 (Exponential Moving Average)"""
    return df[column].ewm(span=period, adjust=False).mean()


def wma(df, period=20, column='Close'):
    """加權移動平均線 (Weighted Moving Average)"""
    weights = np.arange(1, period + 1)
    return df[column].rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def moving_average_cross(df, short=20, long=60, column='Close'):
    """
    均線交叉訊號
    回傳: 1=黃金交叉(短上穿長), -1=死亡交叉(短下穿長), 0=無訊號
    """
    short_ma = sma(df, short, column)
    long_ma = sma(df, long, column)
    
    cross = pd.Series(0, index=df.index)
    cross[(short_ma.shift(1) <= long_ma.shift(1)) & (short_ma > long_ma)] = 1
    cross[(short_ma.shift(1) >= long_ma.shift(1)) & (short_ma < long_ma)] = -1
    return cross


def all_mas(df, column='Close'):
    """
    一次計算常用均線
    回傳 DataFrame 包含 MA5, MA10, MA20, MA60
    """
    result = pd.DataFrame(index=df.index)
    result['MA5'] = sma(df, 5, column)
    result['MA10'] = sma(df, 10, column)
    result['MA20'] = sma(df, 20, column)
    result['MA60'] = sma(df, 60, column)
    return result


def trend_status(df, short=20, long=60, column='Close'):
    """
    判斷趨勢狀態
    回傳: '多頭排列', '空頭排列', '短多頭', '短空頭', '盤整'
    """
    ma20 = sma(df, 20, column).iloc[-1]
    ma60 = sma(df, 60, column).iloc[-1]
    
    if pd.isna(ma20) or pd.isna(ma60):
        return '盤整'
    
    if ma20 > ma60:
        return '多頭排列' if ma20 > ma60 * 1.02 else '短多頭'
    elif ma20 < ma60:
        return '空頭排列' if ma20 < ma60 * 0.98 else '短空頭'
    return '盤整'
