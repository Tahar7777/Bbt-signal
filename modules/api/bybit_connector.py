import requests
import pandas as pd
from datetime import datetime
from modules.utils.data_processor import clean_data

class BybitDataFetcher:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.session = requests.Session()
        
    def get_market_data(self, category='linear'):
        endpoint = "/v5/market/tickers"
        params = {'category': category}
            
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        data = response.json()
        
        if data['retCode'] != 0:
            raise Exception(f"Bybit API Error: {data['retMsg']}")
            
        return self._process_market_data(data['result']['list'])
    
    def _process_market_data(self, raw_data):
        df = pd.DataFrame(raw_data)
        numeric_cols = ['lastPrice', 'price24hPcnt', 'highPrice24h', 'lowPrice24h', 'volume24h']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df['timestamp'] = datetime.utcnow()
        return clean_data(df)
