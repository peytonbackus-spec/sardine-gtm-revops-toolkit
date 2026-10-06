"""
MEDDPICC Health & Risk Calculation Engine
Calculates deal health scores (0-100) and identifies deal progression risks.
"""

class MEDDPICCHealthEngine:
    WEIGHTS = {
        'metrics_verified': 15,
        'economic_buyer_engaged': 25,
        'decision_criteria_documented': 10,
        'decision_process_clear': 10,
        'paper_process_stage': 15,
        'quantified_pain': 15,
        'champion_identified': 10
    }

    @classmethod
    def calculate_deal_health(cls, opp_data):
        score = 0
        risks = []

        if opp_data.get('Quantified_ROI__c'):
            score += cls.WEIGHTS['metrics_verified']
        else:
            risks.append('Missing Quantified ROI Business Case')

        if opp_data.get('Economic_Buyer_Contacted__c'):
            score += cls.WEIGHTS['economic_buyer_engaged']
        else:
            risks.append('No Direct Contact with Economic Buyer')

        if opp_data.get('Quantified_Pain__c'):
            score += cls.WEIGHTS['quantified_pain']
        else:
            risks.append('Quantified Pain Not Identified')

        if opp_data.get('Primary_Champion__c'):
            score += cls.WEIGHTS['champion_identified']
        else:
            risks.append('Primary Champion Missing')

        paper_stage = opp_data.get('Paper_Process_Stage__c', 'Not Started')
        if paper_stage == 'Procurement Approved':
            score += cls.WEIGHTS['paper_process_stage']
        elif paper_stage == 'In Legal Review':
            score += cls.WEIGHTS['paper_process_stage'] // 2

        return {'health_score': score, 'risk_factors': risks, 'qualified_for_stage_4': score >= 65}

if __name__ == '__main__':
    sample_opp = {
        'Quantified_ROI__c': True,
        'Economic_Buyer_Contacted__c': False,
        'Quantified_Pain__c': True,
        'Primary_Champion__c': '0038000000iD34AAAS',
        'Paper_Process_Stage__c': 'In Legal Review'
    }
    result = MEDDPICCHealthEngine.calculate_deal_health(sample_opp)
    print(f"[*] Deal Health Score: {result['health_score']}/100")
    print(f"[*] Identified Risks: {result['risk_factors']}")
