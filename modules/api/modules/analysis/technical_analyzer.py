import pandas as pd
import ta
from ta import add_all_ta_features

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
        
    def analyze(self, df):
        # حساب المؤشرات الأساسية
        df = self._calculate_basic_indicators(df)
        
        # حساب المؤشرات المتقدمة
        df = self._calculate_advanced_indicators(df)
        
        # توليد الإشارات
        signals = self._generate_signals(df)
        
        return signals
    
    def _calculate_basic_indicators(self, df):
        # EMA
        for period in self.config['ema_periods']:
            df[f'ema_{period}'] = ta.trend.EMAIndicator(df['lastPrice'], window=period).ema_indicator()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['lastPrice'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['lastPrice'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        return df
    
    def _calculate_advanced_indicators(self, df):
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['lastPrice'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        # ADX
        df['adx'] = ta.trend.ADXIndicator(
            high=df['highPrice24h'],
            low=df['lowPrice24h'],
            close=df['lastPrice'],
            window=14
        ).adx()
        
        return df
    
    def _generate_signals(self, df):
        signals = []
        
        for _, row in df.iterrows():
            signal = {
                'symbol': row['symbol'],
                'price': row['lastPrice'],
                'timestamp': row['timestamp'].strftime("%Y-%m-%d %H:%M:%S UTC"),
                'confidence': 0,
                'signal': 'NEUTRAL',
                'indicators': {}
            }
            
            bullish, bearish = 0, 0
            
            # تحليل EMA
            ema_signal = "NEUTRAL"
            if row['ema_50'] > row['ema_200']:
                bullish += 1
                ema_signal = "BULLISH"
            else:
                bearish += 1
                ema_signal = "BEARISH"
            signal['indicators']['ema'] = ema_signal
            
            # تحليل RSI
            rsi_signal = "NEUTRAL"
            if row['rsi'] < 30:
                bullish += 1
                rsi_signal = "OVERSOLD"
            elif row['rsi'] > 70:
                bearish += 1
                rsi_signal = "OVERBOUGHT"
            signal['indicators']['rsi'] = rsi_signal
            
            # تحليل MACD
            macd_signal = "NEUTRAL"
            if row['macd'] > row['macd_signal']:
                bullish += 1
                macd_signal = "BULLISH"
            else:
                bearish += 1
                macd_signal = "BEARISH"
            signal['indicators']['macd'] = macd_signal
            
            # تحليل ADX
            if row['adx'] > 25:
                if bullish > bearish:
                    signal['signal'] = 'STRONG_BUY'
                    signal['confidence'] = min(100, (bullish / 3) * 100 + (row['adx'] / 40) * 20)
                elif bearish > bullish:
                    signal['signal'] = 'STRONG_SELL'
                    signal['confidence'] = min(100, (bearish / 3) * 100 + (row['adx'] / 40) * 20)
            
            signals.append(signal)
        
        return signals
