class RiskManager:
    def __init__(self, config):
        self.config = config
        
    def calculate_leverage(self, signal):
        base_leverage = 3
        confidence_factor = signal['confidence'] / 100
        
        leverage = min(
            self.config['max_leverage'],
            round(base_leverage * confidence_factor)
        )
        
        return max(1, leverage)
    
    def calculate_targets(self, signal):
        if 'BUY' in signal['signal']:
            target = signal['price'] * (1 + self.config['target_percentage'])
            stop_loss = signal['price'] * (1 - self.config['stop_loss_percentage'])
        else:
            target = signal['price'] * (1 - self.config['target_percentage'])
            stop_loss = signal['price'] * (1 + self.config['stop_loss_percentage'])
            
        return {
            'target': round(target, 4),
            'stop_loss': round(stop_loss, 4),
            'risk_reward': self.config['target_percentage'] / self.config['stop_loss_percentage']
        }
