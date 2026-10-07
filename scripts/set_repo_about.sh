#!/usr/bin/env bash
# Set the GitHub "About" panel (description, website, topics).
#   bash scripts/set_repo_about.sh        (needs the GitHub CLI: brew install gh && gh auth login)
set -euo pipefail
REPO="peytonbackus-spec/sardine-gtm-revops-toolkit"
DESC="RevOps + GTM engineering toolkit for Sardine's consumption-priced fraud & AML platform: scoring, routing, pipeline, forecast, usage-vs-commit and renewals, plus VP of Sales briefs, stage bottlenecks, capacity/quota/territory planning and Marketing Ops attribution. Salesforce · HubSpot · Unify · Clay · n8n. Synthetic data."
TOPICS=(revenue-operations revops gtm-engineering salesforce hubspot clay n8n lead-scoring lead-routing
        forecasting usage-based-pricing fraud-prevention aml ai-governance python sql
        sales-analytics pipeline-analytics capacity-planning marketing-operations)

if ! command -v gh >/dev/null; then
  echo "GitHub CLI not found. Set it by hand: repo page -> gear icon next to 'About'."
  echo "Description: $DESC"
  echo "Website:     https://github.com/${REPO}/wiki"
  echo "Topics:      ${TOPICS[*]}"
  exit 0
fi
args=()
for t in "${TOPICS[@]}"; do args+=(--add-topic "$t"); done
gh repo edit "$REPO" --description "$DESC" --homepage "https://github.com/${REPO}/wiki" --enable-wiki "${args[@]}"
echo "About panel updated: https://github.com/${REPO}"
