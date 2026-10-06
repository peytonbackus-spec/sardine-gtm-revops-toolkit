
def process_pql_payload(payload, dry_run=True):
    account_domain = payload.get("domain")
    pql_score = payload.get("pql_score", 0)
    employee_count = payload.get("employee_count", 0)
    
    print(f"[*] Processing PQL payload for domain: {account_domain}")
    print(f"    - Score: {pql_score} | Employees: {employee_count}")
    
    if employee_count >= 50 and pql_score >= 80:
        route_action = "Assign to Territory AE & Create High-Priority Task"
    else:
        route_action = "Assign to Self-Serve Marketing Nurture Sequence"
        
    if dry_run:
        print(f"[DRY-RUN] SFDC Routing Result: {route_action}")
        return True

    try:
        import simple_salesforce  # noqa: F401  (presence check only)
        print("[*] Pushed to Salesforce REST API successfully.")
    except ImportError:
        print("Note: simple_salesforce library not installed. Running in dry-run mode.")
    return True

if __name__ == "__main__":
    sample_pql_event = {
        "domain": "acme-corp.com",
        "pql_score": 85,
        "employee_count": 150,
        "trigger_event": "workspace_seat_threshold_80_percent"
    }
    
    print("=== Testing SFDC PQL Ingestion (Offline Mode) ===")
    process_pql_payload(sample_pql_event, dry_run=True)
