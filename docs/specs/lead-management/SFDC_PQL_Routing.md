# Salesforce (SFDC) Product-Qualified Lead (PQL) Routing Architecture

## System Integrations
- **Source**: Product Event Telemetry / Segment / Webhook
- **Middleware**: Workato / Zapier / Salesforce REST API
- **Destination**: Salesforce Lead/Contact & Account Objects

## PQL Ingestion & Routing Logic
1. **Account Matching**: Incoming domain matches `Account.Website` or `Account.Domain__c`.
2. **Lead/Contact Creation**: Upserts Lead or Contact associated with the target Account.
3. **PQL Scoring & Assignment**:
   - If `Account.Employee_Count__c >= 50` AND `Account.PQL_Score__c >= 80`:
     - Assign via SFDC Assignment Rules to Territory AE.
     - Auto-create high-priority `Task` assigned to Account Owner: `"PQL Spike: High usage detected"`.
   - If Account is under threshold:
     - Route to Self-Serve Nurture campaign via Marketing Automation.
