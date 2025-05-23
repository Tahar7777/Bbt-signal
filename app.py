from flask import Flask, render_template, jsonify
from modules.api.bybit_connector import BybitDataFetcher
from modules.analysis.technical_analyzer import TechnicalAnalyzer
from modules.analysis.risk_manager import RiskManager
from config import CONFIG
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# تهيئة المكونات
data_fetcher = BybitDataFetcher()
analyzer = TechnicalAnalyzer(CONFIG['analysis'])
risk_manager = RiskManager(CONFIG['risk'])

# تخزين الإشارات
signals = []
last_update = None

def fetch_and_analyze():
    global signals, last_update
    while True:
        try:
            print("جلب البيانات من Bybit...")
            market_data = data_fetcher.get_market_data()
            
            print("تحليل البيانات...")
            raw_signals = analyzer.analyze(market_data)
            
            current_signals = []
            for signal in raw_signals:
                if 'STRONG' in signal['signal']:
                    risk_data = risk_manager.calculate_targets(signal)
                    leverage = risk_manager.calculate_leverage(signal)
                    
                    signal.update({
                        'leverage': leverage,
                        **risk_data
                    })
                    current_signals.append(signal)
            
            signals = current_signals
            last_update = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"تم التحديث في {last_update}")
            
        except Exception as e:
            print(f"حدث خطأ: {str(e)}")
        
        time.sleep(CONFIG['scan_interval'])

@app.route('/')
def index():
    return render_template('index.html', signals=signals, last_update=last_update)

@app.route('/api/signals')
def get_signals():
    return jsonify({
        'signals': signals,
        'last_update': last_update
    })

if __name__ == '__main__':
    # بدء عملية المسح في خيط منفصل
    scanner_thread = threading.Thread(target=fetch_and_analyze)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # بدء خادم Flask
    app.run(host='0.0.0.0', port=5000)
