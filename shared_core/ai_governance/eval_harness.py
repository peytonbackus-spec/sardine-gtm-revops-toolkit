"""Offline eval harness for AI workflows.

Role scope: define prompts, outputs, evaluation criteria and human-in-the-loop
controls (GTM Engineer); prompt design, testing and monitoring (Strategy & Ops).

An eval case is a fixed input record plus the checks its output must pass. The
harness runs a workflow function over every case and scores it. Run it on every
prompt change (CI does this) so a prompt edit that breaks the contract fails the
build instead of reaching a rep.

Check types:
  required_keys     output must contain these keys
  enum              {key: [allowed values]}
  must_not_contain  phrases that signal overclaiming or unsafe output
  no_pii            output text must not contain PII patterns
  min_items         {key: n}, e.g. at least one evidence item
  expect            {key: value}, exact-match expectations for deterministic fields
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from shared_core.ai_governance.pii_guard import contains_pii


def check_output(out: dict, checks: dict) -> list[str]:
    errors = []
    for k in checks.get("required_keys", []):
        if k not in out:
            errors.append(f"missing key '{k}'")
    for k, allowed in checks.get("enum", {}).items():
        if k in out and out[k] not in allowed:
            errors.append(f"'{k}'={out[k]!r} not in {allowed}")
    blob = json.dumps(out).lower()
    for phrase in checks.get("must_not_contain", []):
        if phrase.lower() in blob:
            errors.append(f"contains banned phrase '{phrase}'")
    if checks.get("no_pii") and contains_pii(json.dumps(out)):
        errors.append("output contains PII")
    for k, n in checks.get("min_items", {}).items():
        if len(out.get(k) or []) < n:
            errors.append(f"'{k}' has fewer than {n} items")
    for k, v in checks.get("expect", {}).items():
        if out.get(k) != v:
            errors.append(f"expected {k}={v!r}, got {out.get(k)!r}")
    return errors


def run_evals(cases_path: str | Path, workflow: Callable[[dict], dict]) -> dict:
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    results = []
    for case in cases:
        try:
            out = workflow(case["record"])
            errors = check_output(out, case["checks"])
        except Exception as exc:  # a crash is a failed case, not a crashed harness
            errors = [f"exception: {exc}"]
        results.append({"case": case["id"], "passed": not errors, "errors": "; ".join(errors)})
    passed = sum(r["passed"] for r in results)
    return {"cases": results, "passed": passed, "total": len(results),
            "pass_rate": round(100 * passed / len(results), 1) if results else 0.0}
