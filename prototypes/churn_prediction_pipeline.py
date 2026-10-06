"""
Account Churn Risk & Retention Intelligence Engine
Evaluates account health telemetry to compute churn risk probability.
"""

class AccountChurnPredictor:
    def __init__(self, telemetry_data):
        self.telemetry = telemetry_data

    def predict_risk(self):
        score = 100
        flags = []

        # Weekly Active User (WAU) decay check
        wau_change = self.telemetry.get('wau_change_pct', 0)
        if wau_change < -20:
            score -= 30
            flags.append(f'Severe WAU Decay: {wau_change}% over 30 days')

        # Executive sponsor status
        if not self.telemetry.get('has_active_exec_sponsor', True):
            score -= 25
            flags.append('Executive Sponsor Departed or Inactive')

        # Escalated support tickets
        open_escalations = self.telemetry.get('open_escalated_tickets', 0)
        if open_escalations > 0:
            score -= (open_escalations * 15)
            flags.append(f'{open_escalations} Unresolved High-Severity Support Tickets')

        risk_level = 'CRITICAL' if score < 50 else 'ELEVATED' if score < 75 else 'LOW'
        
        return {
            'account_id': self.telemetry.get('account_id'),
            'health_score': max(score, 0),
            'risk_level': risk_level,
            'churn_risk_factors': flags
        }

if __name__ == '__main__':
    sample_telemetry = {
        'account_id': '0018000000K99ZZ',
        'wau_change_pct': -35.5,
        'has_active_exec_sponsor': False,
        'open_escalated_tickets': 1
    }

    predictor = AccountChurnPredictor(sample_telemetry)
    result = predictor.predict_risk()
    print(f'[*] Account Risk Assessment: {result}')
