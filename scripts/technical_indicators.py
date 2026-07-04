"""
technical_indicators.py - 技術指標整合介面

統一匯入所有技術指標模組，提供與 plot_stock 資料格式相容的函數。
plot_stock 資料格式: pandas DataFrame with 'Close', 'High', 'Low', 'Volume' columns
"""
import pandas as pd
import numpy as np

import sys
import os

# 確保 technical 目錄在路徑中
_current_dir = os.path.dirname(__file__)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from technical import moving_averages as ma
from technical import rsi as rsi_module
from technical import macd as macd_module
from technical import bollinger_bands as bb_module
from technical import kd as kd_module

from strategies import volume_breakout as vb_module
from strategies import ma_breakthrough as mab_module
from backtest import simple_backtest as bt_module


# === 統一計算函數 ===

def calculate_all(df):
    """
    計算所有技術指標
    
    參數:
        df: DataFrame with 'Close', 'High', 'Low', 'Volume' columns
    
    回傳: dict 含所有技術指標最新值
    """
    if df.empty or len(df) < 20:
        return {
            'ma20': '-', 'ma60': '-', 'rsi': '-', 'trend': '資料不足',
            'macd': {'dif': '-', 'dea': '-', 'hist': '-', 'score': '-', 'signal': '-'},
            'kd': {'k': '-', 'd': '-', 'signal': '-'},
            'bollinger': {'upper': '-', 'middle': '-', 'lower': '-', 'position': '-', 'position_text': '-'},
        }
    
    result = {}
    
    # 移動平均線
    mas = ma.all_mas(df)
    result['ma20'] = round(mas['MA20'].iloc[-1], 2) if not pd.isna(mas['MA20'].iloc[-1]) else '-'
    result['ma60'] = round(mas['MA60'].iloc[-1], 2) if not pd.isna(mas['MA60'].iloc[-1]) else '-'
    result['trend'] = ma.trend_status(df)
    
    # RSI
    rsi_val = rsi_module.rsi(df).iloc[-1]
    result['rsi'] = round(rsi_val, 1) if not pd.isna(rsi_val) else '-'
    
    # MACD
    result['macd'] = macd_module.macd_summary(df)
    
    # KD
    result['kd'] = kd_module.kd_summary(df)
    
    # 布林通道
    result['bollinger'] = bb_module.bollinger_summary(df)
    
    # 乖離率
    close = df['Close'].iloc[-1]
    if isinstance(result['ma20'], (int, float)) and result['ma20'] != 0:
        result['bias20'] = round((close - result['ma20']) / result['ma20'] * 100, 2)
    else:
        result['bias20'] = '-'
    
    if isinstance(result['ma60'], (int, float)) and result['ma60'] != 0:
        result['bias60'] = round((close - result['ma60']) / result['ma60'] * 100, 2)
    else:
        result['bias60'] = '-'
    
    return result


def generate_signals(df):
    """
    生成綜合交易訊號
    
    回傳: dict 含各策略訊號與綜合評分
    """
    if df.empty or len(df) < 20:
        return {'overall': '資料不足', 'score': 50, 'details': {}}
    
    signals = {}
    score = 50
    
    # 均線交叉
    ma_cross = ma.moving_average_cross(df).iloc[-1]
    if ma_cross == 1:
        signals['ma_cross'] = '黃金交叉 (買入)'
        score += 15
    elif ma_cross == -1:
        signals['ma_cross'] = '死亡交叉 (賣出)'
        score -= 15
    else:
        signals['ma_cross'] = '無訊號'
    
    # RSI
    rsi_val = rsi_module.rsi(df).iloc[-1]
    if not pd.isna(rsi_val):
        if rsi_val < 30:
            signals['rsi'] = 'RSI 超賣 (買入)'
            score += 10
        elif rsi_val > 70:
            signals['rsi'] = 'RSI 超買 (賣出)'
            score -= 10
        else:
            signals['rsi'] = 'RSI 正常'
    else:
        signals['rsi'] = '無資料'
    
    # MACD
    macd_signal = macd_module.macd_signal(df).iloc[-1]
    if macd_signal == 1:
        signals['macd'] = 'MACD 黃金交叉 (買入)'
        score += 15
    elif macd_signal == -1:
        signals['macd'] = 'MACD 死亡交叉 (賣出)'
        score -= 15
    else:
        signals['macd'] = 'MACD 無訊號'
    
    # KD
    kd_signal = kd_module.kd_signal(df).iloc[-1]
    if kd_signal == 1:
        signals['kd'] = 'KD 黃金交叉 (買入)'
        score += 10
    elif kd_signal == -1:
        signals['kd'] = 'KD 死亡交叉 (賣出)'
        score -= 10
    else:
        signals['kd'] = 'KD 無訊號'
    
    # 布林通道
    bb_pos = bb_module.bollinger_position(df)
    if bb_pos == 'lower_band':
        signals['bollinger'] = '觸及下軌 (買入)'
        score += 10
    elif bb_pos == 'upper_band':
        signals['bollinger'] = '觸及上軌 (賣出)'
        score -= 10
    else:
        signals['bollinger'] = f'布林{bb_pos}'
    
    # 量能突破
    vb_info = vb_module.volume_breakout_info(df)
    if vb_info['is_breakout']:
        signals['volume'] = '量能突破 (買入)'
        score += 10
    else:
        signals['volume'] = '量能正常'
    
    # 均線突破
    mab_info = mab_module.ma_breakthrough_info(df)
    if mab_info['is_breakthrough'] and mab_info['is_bullish']:
        signals['ma_break'] = '均線突破 (買入)'
        score += 10
    else:
        signals['ma_break'] = mab_info['signal']
    
    # 綜合評分
    score = max(0, min(100, score))
    
    if score >= 80:
        overall = '強烈偏多'
    elif score >= 60:
        overall = '偏多'
    elif score <= 20:
        overall = '強烈偏空'
    elif score <= 40:
        overall = '偏空'
    else:
        overall = '盤整'
    
    return {
        'overall': overall,
        'score': score,
        'details': signals
    }


# === 便捷函數 ===

def get_ma(df, period=20, column='Close'):
    """取得單一均線值"""
    return ma.sma(df, period, column).iloc[-1]


def get_rsi(df, period=14, column='Close'):
    """取得 RSI 值"""
    val = rsi_module.rsi(df, period, column).iloc[-1]
    return round(val, 1) if not pd.isna(val) else '-'


def get_macd(df, fast=12, slow=26, signal=9, column='Close'):
    """取得 MACD 摘要"""
    return macd_module.macd_summary(df, fast, slow, signal, column)


def get_kd(df, n=9, m1=3, m2=3):
    """取得 KD 摘要"""
    return kd_module.kd_summary(df, n, m1, m2)


def get_bollinger(df, period=20, std_dev=2, column='Close'):
    """取得布林通道摘要"""
    return bb_module.bollinger_summary(df, period, std_dev, column)


def backtest(df, strategy='ma_cross', params=None, initial_capital=1000000):
    """
    便捷回測函數
    """
    return bt_module.backtest_strategy(df, strategy, params, initial_capital)
