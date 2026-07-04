"""
simple_backtest.py - 簡易回測框架

使用方式:
    from simple_backtest import BacktestEngine
    engine = BacktestEngine(df)
    engine.add_strategy('ma_cross', {'short': 20, 'long': 60})
    result = engine.run()
"""
import pandas as pd
import numpy as np
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from technical import moving_averages, rsi, macd, bollinger_bands, kd


class BacktestEngine:
    """簡易回測引擎"""
    
    def __init__(self, df, initial_capital=1000000):
        """
        df: pandas DataFrame with 'Close', 'High', 'Low', 'Volume' columns
        initial_capital: 初始資金 (預設 100萬)
        """
        self.df = df.copy()
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.trades = []
        self.signals = pd.Series(0, index=df.index)
        
    def add_strategy(self, strategy_name, params=None):
        """
        添加策略
        strategy_name: 'ma_cross', 'rsi_reversal', 'macd_cross', 'bollinger_bounce', 'kd_cross'
        params: 策略參數 dict
        """
        if params is None:
            params = {}
        
        df = self.df
        
        if strategy_name == 'ma_cross':
            short = params.get('short', 20)
            long = params.get('long', 60)
            self.signals = moving_averages.moving_average_cross(df, short, long)
            
        elif strategy_name == 'rsi_reversal':
            period = params.get('period', 14)
            overbought = params.get('overbought', 70)
            oversold = params.get('oversold', 30)
            self.signals = rsi.rsi_signal(df, period, overbought=overbought, oversold=oversold)
            
        elif strategy_name == 'macd_cross':
            self.signals = macd.macd_signal(df)
            
        elif strategy_name == 'bollinger_bounce':
            self.signals = bollinger_bands.bollinger_signal(df)
            
        elif strategy_name == 'kd_cross':
            self.signals = kd.kd_signal(df)
            
        elif strategy_name == 'volume_breakout':
            # 量能突破: 成交量 > 5日均量 1.5倍 且 收漲
            vol_ma = df['Volume'].rolling(5).mean()
            self.signals = pd.Series(0, index=df.index)
            self.signals[(df['Volume'] > vol_ma * 1.5) & (df['Close'] > df['Close'].shift(1))] = 1
            
        elif strategy_name == 'ma_breakthrough':
            # 均線突破: 收盤價突破 MA20
            ma20 = moving_averages.sma(df, 20)
            self.signals = pd.Series(0, index=df.index)
            self.signals[(df['Close'] > ma20) & (df['Close'].shift(1) <= ma20.shift(1))] = 1
        
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    def run(self, commission=0.001425, tax=0.003):
        """
        執行回測
        commission: 手續費 (預設 0.1425%)
        tax: 交易稅 (預設 0.3%)
        回傳: dict with results
        """
        df = self.df
        capital = self.initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []
        
        for i in range(1, len(df)):
            date = df.index[i]
            price = df['Close'].iloc[i]
            signal = self.signals.iloc[i]
            
            # 買入訊號
            if signal == 1 and position == 0:
                position = 1
                entry_price = price
                cost = price * (1 + commission)
                trades.append({
                    'type': 'buy',
                    'date': str(date)[:10] if hasattr(date, 'strftime') else str(date),
                    'price': price,
                    'cost': cost
                })
            
            # 賣出訊號 (簡化: 用相反訊號或持有一段時間)
            elif signal == -1 and position == 1:
                position = 0
                sell_price = price * (1 - commission - tax)
                pnl = sell_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                trades.append({
                    'type': 'sell',
                    'date': str(date)[:10] if hasattr(date, 'strftime') else str(date),
                    'price': price,
                    'sell_price': sell_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
            
            # 計算當前權益
            if position == 1:
                equity = capital + (price - entry_price) / entry_price * capital
            else:
                equity = capital
            equity_curve.append(equity)
        
        # 計算績效指標
        if len(trades) >= 2:
            # 只計算完整交易 (有買有賣)
            complete_trades = []
            for i in range(1, len(trades)):
                if trades[i-1]['type'] == 'buy' and trades[i]['type'] == 'sell':
                    complete_trades.append({
                        'entry_date': trades[i-1]['date'],
                        'exit_date': trades[i]['date'],
                        'entry_price': trades[i-1]['price'],
                        'exit_price': trades[i]['price'],
                        'pnl': trades[i]['pnl'],
                        'pnl_pct': trades[i]['pnl_pct']
                    })
            
            if complete_trades:
                wins = [t for t in complete_trades if t['pnl'] > 0]
                losses = [t for t in complete_trades if t['pnl'] <= 0]
                win_rate = len(wins) / len(complete_trades) * 100 if complete_trades else 0
                total_return = sum(t['pnl_pct'] for t in complete_trades)
                avg_return = total_return / len(complete_trades)
                
                # 最大回撤
                max_drawdown = 0
                peak = equity_curve[0] if equity_curve else self.initial_capital
                for eq in equity_curve:
                    if eq > peak:
                        peak = eq
                    drawdown = (peak - eq) / peak * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                
                return {
                    'total_trades': len(complete_trades),
                    'win_count': len(wins),
                    'loss_count': len(losses),
                    'win_rate': round(win_rate, 2),
                    'total_return': round(total_return, 2),
                    'avg_return': round(avg_return, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'trades': complete_trades,
                    'equity_curve': [round(e, 2) for e in equity_curve],
                }
        
        return {
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'win_rate': 0,
            'total_return': 0,
            'avg_return': 0,
            'max_drawdown': 0,
            'trades': [],
            'equity_curve': [],
        }


def backtest_strategy(df, strategy_name, params=None, initial_capital=1000000):
    """
    便捷函數：單一策略回測
    """
    engine = BacktestEngine(df, initial_capital)
    engine.add_strategy(strategy_name, params)
    return engine.run()


def backtest_all(df, initial_capital=1000000):
    """
    回測所有策略，回傳比較結果
    """
    strategies = {
        '均線交叉 (MA20/MA60)': {'name': 'ma_cross', 'params': {'short': 20, 'long': 60}},
        'RSI 逆轉 (30/70)': {'name': 'rsi_reversal', 'params': {'period': 14, 'overbought': 70, 'oversold': 30}},
        'MACD 交叉': {'name': 'macd_cross', 'params': {}},
        '布林反彈': {'name': 'bollinger_bounce', 'params': {}},
        'KD 交叉': {'name': 'kd_cross', 'params': {}},
    }
    
    results = {}
    for label, cfg in strategies.items():
        result = backtest_strategy(df, cfg['name'], cfg['params'], initial_capital)
        results[label] = result
    
    return results
