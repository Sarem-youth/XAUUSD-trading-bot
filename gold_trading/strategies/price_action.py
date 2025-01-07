import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class PASignal:
    strength: float
    direction: str
    pattern: str
    timeframe: str

class PriceActionAnalyzer:
    def __init__(self, symbol, timeframes, cache_manager=None):
        self.symbol = symbol
        self.timeframes = timeframes
        self.cache = cache_manager
        self.last_api_call = datetime.now()
        
    def get_data(self, timeframe, bars=100):
        cache_key = f"{self.symbol}_{timeframe}_{bars}"
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
                
        # Rate limiting
        elapsed = (datetime.now() - self.last_api_call).total_seconds()
        if elapsed < settings.API_CALL_DELAY:
            time.sleep(settings.API_CALL_DELAY - elapsed)
            
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, bars)
        df = pd.DataFrame(rates)
        
        if self.cache:
            self.cache.set(cache_key, df)
            
        self.last_api_call = datetime.now()
        return df

    def analyze_all_timeframes(self):
        signals = []
        for tf in self.timeframes:
            df = self.get_data(tf)
            zones = self.analyze_supply_demand(df)
            patterns = self.detect_patterns(df)
            signals.append(self._combine_analysis(zones, patterns, tf))
        return signals

    def analyze_supply_demand(self, df, lookback=20):
        zones = []
        volatility = df['high'].rolling(lookback).std()
        
        for i in range(lookback, len(df)-1):
            if (df['high'].iloc[i] > df['high'].iloc[i-lookback:i].max() and
                df['volume'].iloc[i] > df['volume'].iloc[i-lookback:i].mean() * 1.5):
                zones.append({
                    'type': 'supply',
                    'price': df['high'].iloc[i],
                    'strength': volatility.iloc[i]
                })
            
            if (df['low'].iloc[i] < df['low'].iloc[i-lookback:i].min() and
                df['volume'].iloc[i] > df['volume'].iloc[i-lookback:i].mean() * 1.5):
                zones.append({
                    'type': 'demand',
                    'price': df['low'].iloc[i],
                    'strength': volatility.iloc[i]
                })
        return zones

    def detect_patterns(self, df):
        bullish_eng = (df['open'].shift(1) > df['close'].shift(1)) & \
                     (df['close'] > df['open']) & \
                     (df['close'] > df['open'].shift(1)) & \
                     (df['open'] < df['close'].shift(1))
        
        bearish_eng = (df['open'].shift(1) < df['close'].shift(1)) & \
                     (df['close'] < df['open']) & \
                     (df['close'] < df['open'].shift(1)) & \
                     (df['open'] > df['close'].shift(1))

        return {
            'bullish_engulfing': bullish_eng,
            'bearish_engulfing': bearish_eng
        }

    def _combine_analysis(self, zones, patterns, timeframe):
        # Enhanced signal generation with less dependency on external data
        signal_strength = 0.0
        direction = "NONE"
        
        # Calculate signal based on technical patterns only
        recent_zones = [z for z in zones if z['strength'] > np.mean([x['strength'] for x in zones])]
        
        if recent_zones:
            latest_zone = recent_zones[-1]
            direction = "SELL" if latest_zone['type'] == 'supply' else "BUY"
            signal_strength = latest_zone['strength']
            
        if patterns['bullish_engulfing'].iloc[-1] and direction != "SELL":
            signal_strength += 0.2
            direction = "BUY"
        elif patterns['bearish_engulfing'].iloc[-1] and direction != "BUY":
            signal_strength += 0.2
            direction = "SELL"
            
        return PASignal(
            strength=min(signal_strength, 1.0),
            direction=direction,
            pattern="technical",
            timeframe=str(timeframe)
        )
