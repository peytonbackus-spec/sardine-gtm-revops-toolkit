"""
RevOps Schema Tech Debt & Metadata Governance Auditor
Analyzes Salesforce field utilization and identifies fields slated for deprecation.
"""

from datetime import datetime
from typing import Any, Dict, List


class RevOpsTechDebtAuditor:

    def __init__(self, schema_telemetry: List[Dict[str, Any]]):
        self.schema_telemetry = schema_telemetry

    def run_schema_audit(self) -> List[Dict[str, Any]]:
        audit_results = []
        for field in self.schema_telemetry:
            api_name = field.get('api_name')
            fill_rate = field.get('population_rate_pct', 0.0)
            days_inactive = field.get('days_since_last_modified', 0)

            if fill_rate < 5.0 and days_inactive > 180:
                severity = 'HIGH'
                action = 'DEPRECATE_IMMEDIATELY'
            elif fill_rate < 15.0 or days_inactive > 90:
                severity = 'MEDIUM'
                action = 'REVIEW_WITH_BUSINESS_OWNER'
            else:
                severity = 'LOW'
                action = 'RETAIN'

            if severity in ['HIGH', 'MEDIUM']:
                audit_results.append({
                    'api_name': api_name,
                    'population_rate_pct': fill_rate,
                    'days_inactive': days_inactive,
                    'severity': severity,
                    'recommended_action': action
                })

        return audit_results

    def generate_markdown_report(self, audit_results: List[Dict[str, Any]]) -> str:
        lines = [
            '# Salesforce Schema Tech Debt Audit Report',
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d')}*",
            '',
            '| Field API Name | Fill Rate (%) | Inactive Days | Severity | Action |',
            '| :--- | :--- | :--- | :--- | :--- |'
        ]

        for item in audit_results:
            lines.append(
                f"| `{item['api_name']}` | {item['population_rate_pct']}% | "
                f"{item['days_inactive']} | **{item['severity']}** | `{item['recommended_action']}` |"
            )

        return '\n'.join(lines)


if __name__ == '__main__':
    sample_schema = [
        {'api_name': 'Legacy_Lead_Score__c', 'population_rate_pct': 1.2, 'days_since_last_modified': 210},
        {'api_name': 'MEDDPICC_Health_Score__c', 'population_rate_pct': 94.5, 'days_since_last_modified': 2},
        {'api_name': 'Old_Campaign_ID__c', 'population_rate_pct': 12.0, 'days_since_last_modified': 110}
    ]

    auditor = RevOpsTechDebtAuditor(sample_schema)
    results = auditor.run_schema_audit()
    print(auditor.generate_markdown_report(results))
