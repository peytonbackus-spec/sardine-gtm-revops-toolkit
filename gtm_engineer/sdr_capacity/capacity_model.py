"""SDR capacity model: work backward from the pipeline target to headcount and activity.

Role scope (GTM Engineer): partner with SDR leadership on capacity and performance goals.

Inputs are the funnel rates the funnel report measures, so the model updates
itself as conversion changes instead of using a planning number from last year.
Every input is an argument; the defaults are illustrative [ASSUME] values, to be
replaced with the company's actuals in week one.

    python -m gtm_engineer.sdr_capacity.capacity_model --pipeline-target 6000000
"""
from __future__ import annotations

import argparse
import math


def capacity(pipeline_target: float, avg_opp_size: float, sql_to_opp: float, meeting_to_sql: float,
             inbound_share: float, sdr_meetings_per_month: float, ramp_months: int = 3, months: int = 3,
             connects_per_meeting: float = 9, dials_per_connect: float = 14) -> dict:
    opps_needed = pipeline_target / avg_opp_size
    sqls_needed = opps_needed / sql_to_opp
    meetings_needed = sqls_needed / meeting_to_sql
    outbound_meetings = meetings_needed * (1 - inbound_share)
    per_month = meetings_needed / months
    # a rep hired today produces ~half capacity on average across a 3-month ramp
    ramp_factor = 1 - (ramp_months / months) * 0.5 if months > ramp_months else 0.5
    sdrs = per_month / sdr_meetings_per_month
    return {
        "opps_needed": math.ceil(opps_needed), "sqls_needed": math.ceil(sqls_needed),
        "meetings_needed": math.ceil(meetings_needed), "outbound_meetings": math.ceil(outbound_meetings),
        "meetings_per_month": round(per_month, 1), "ramped_sdrs_needed": round(sdrs, 1),
        "if_hiring_now_sdrs_needed": round(sdrs / ramp_factor, 1),
        "monthly_dials_outbound": math.ceil(outbound_meetings / months * connects_per_meeting * dials_per_connect),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pipeline-target", type=float, default=6_000_000, help="SDR+marketing sourced pipeline $ for the quarter")
    ap.add_argument("--avg-opp-size", type=float, default=105_000)
    ap.add_argument("--sql-to-opp", type=float, default=0.55)
    ap.add_argument("--meeting-to-sql", type=float, default=0.60)
    ap.add_argument("--inbound-share", type=float, default=0.45)
    ap.add_argument("--sdr-meetings-per-month", type=float, default=14)
    a = ap.parse_args()
    out = capacity(a.pipeline_target, a.avg_opp_size, a.sql_to_opp, a.meeting_to_sql, a.inbound_share, a.sdr_meetings_per_month)
    print(f"=== Capacity to source ${a.pipeline_target:,.0f} in a quarter ===")
    for k, v in out.items():
        print(f"  {k:<28} {v}")
    print("\nSensitivity: meeting->SQL conversion")
    for rate in (0.45, 0.55, 0.65, 0.75):
        r = capacity(a.pipeline_target, a.avg_opp_size, a.sql_to_opp, rate, a.inbound_share, a.sdr_meetings_per_month)
        print(f"  {rate:.0%}: {r['ramped_sdrs_needed']} ramped SDRs, {r['meetings_needed']} meetings")


if __name__ == "__main__":
    main()
