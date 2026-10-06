# PLG Product-Qualified Lead (PQL) Routing Framework

## PQL Triggers
- **Account Expansion**: Workspace reaches >= 80% seat limit within 14 days.
- **Feature Velocity**: Workspace triggers 3+ premium integration attempts in 7 days.
- **Power User Density**: 5+ active daily users within a single corporate domain.

## Routing Workflow
1. Product webhook sends usage payload to HubSpot.
2. Workflow verifies ICP criteria (Employee Count > 50, Target Tech Stack match).
3. Auto-creates High-Priority Sales Task assigned to territory AE.
