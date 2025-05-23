from flask import Flask, render_template, jsonify
import requests
import pandas as pd
import ta
from datetime import datetime
import threading
import time
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # استبدلها بمفتاح حقيقي في الإنتاج

# إعداد نظام التسجيل (Logging)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# إعدادات التطبيق
CONFIG = {
    'scan_interval': 300,  # 5 دقائق بين كل مسح
    'api_url': 'https://api.bybit.com/v5/market/tickers?category=linear',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# تخزين البيانات
signals = []
last_update = None

def fetch_bybit_data():
    """جلب البيانات من واجهة Bybit العامة"""
    headers = {'User-Agent': CONFIG['user_agent']}
    try:
        response = requests.get(CONFIG['api_url'], headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('retCode') != 0:
            app.logger.error(f"Bybit API Error: {data.get('retMsg', 'Unknown error')}")
            return None
            
        return pd.DataFrame(data['result']['list'])
    except Exception as e:
        app.logger.error(f"Failed to fetch data: {str(e)}")
        return None

def calculate_indicators(df):
    """حساب المؤشرات الفنية"""
    if df is None or df.empty:
        return []
    
    try:
        # تحويل الأعمدة الرقمية
        numeric_cols = ['lastPrice', 'highPrice24h', 'lowPrice24h', 'volume24h']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # حساب المؤشرات
        df['ema_50'] = ta.trend.EMAIndicator(df['lastPrice'], window=50).ema_indicator()
        df['ema_200'] = ta.trend.EMAIndicator(df['lastPrice'], window=200).ema_indicator()
        df['rsi'] = ta.momentum.RSIIndicator(df['lastPrice'], window=14).rsi()
        
        macd = ta.trend.MACD(df['lastPrice'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        return df.to_dict('records')
    except Exception as e:
        app.logger.error(f"Indicator calculation error: {str(e)}")
        return []

def generate_signals(data):
    """توليد إشارات التداول"""
    signals = []
    for item in data:
        try:
            signal = {
                'symbol': item['symbol'],
                'price': float(item['lastPrice']),
                'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                'signal': 'NEUTRAL',
                'confidence': 0,
                'indicators': {}
            }
            
            # تحليل المؤشرات
            bullish = 0
            
            # تحليل EMA
            if item['ema_50'] > item['ema_200']:
                bullish += 1
                signal['indicators']['ema'] = 'BULLISH'
            else:
                signal['indicators']['ema'] = 'BEARISH'
                
            # تحليل RSI
            if item['rsi'] < 30:
                bullish += 1
                signal['indicators']['rsi'] = 'OVERSOLD'
            elif item['rsi'] > 70:
                signal['indicators']['rsi'] = 'OVERBOUGHT'
            else:
                signal['indicators']['rsi'] = 'NEUTRAL'
                
            # تحليل MACD
            if item['macd'] > item['macd_signal']:
                bullish += 1
                signal['indicators']['macd'] = 'BULLISH'
            else:
                signal['indicators']['macd'] = 'BEARISH'
            
            # تحديد الإشارة النهائية
            if bullish >= 2:
                signal['signal'] = 'BUY'
                signal['confidence'] = min(100, bullish * 30)
                signals.append(signal)
                
        except Exception as e:
            app.logger.error(f"Signal generation error for {item.get('symbol')}: {str(e)}")
    
    return signals

def background_scanner():
    """المسح الخلفي للبيانات"""
    global signals, last_update
    while True:
        try:
            app.logger.info("جلب البيانات من Bybit...")
            data = fetch_bybit_data()
            
            if data is not None:
                app.logger.info("معالجة البيانات...")
                processed_data = calculate_indicators(data)
                signals = generate_signals(processed_data)
                last_update = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                app.logger.info(f"تم التحديث - {len(signals)} إشارة وجدت")
            
        except Exception as e:
            app.logger.error(f"Scanner error: {str(e)}")
        
        time.sleep(CONFIG['scan_interval'])

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html', 
                         signals=signals, 
                         last_update=last_update,
                         config=CONFIG)

@app.route('/api/signals')
def api_signals():
    """واجهة API للإشارات"""
    return jsonify({
        'status': 'success',
        'data': signals,
        'last_update': last_update,
        'count': len(signals)
    })

if __name__ == '__main__':
    # بدء المسح الخلفي في خيط منفصل
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # بدء خادم Flask
    app.run(host='0.0.0.0', port=5000, debug=False)
