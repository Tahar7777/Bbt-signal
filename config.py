CONFIG = {
    'scan_interval': 300,  # 5 دقائق بين كل مسح
    'analysis': {
        'ema_periods': [9, 20, 50, 100, 200],
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'adx_period': 14,
        'min_confidence': 70
    },
    'risk': {
        'target_percentage': 0.015,  # 1.5%
        'stop_loss_percentage': 0.005,  # 0.5%
        'max_leverage': 10,
        'volatility_threshold': 0.05
    }
}
