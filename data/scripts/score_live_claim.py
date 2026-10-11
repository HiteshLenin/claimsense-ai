"""Test the live-claim mapping end to end.

Run from the project root:
    python data/scripts/score_live_claim.py
"""
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path("backend").resolve()))
from app.services.risk import claim_to_model_input, ml_fraud_score  # noqa: E402

# Stand-in for the real POL-100234 row (same values):
claim = SimpleNamespace(
    policy_number="POL-100234",
    loss_date=datetime(2026, 9, 20, 10, 30),
    loss_type="collision",
    description="Rear-end collision at intersection; bumper and taillight damage",
    amount=2450.00,
)

features = claim_to_model_input(claim)
print("Fields taken from the live claim:")
for k in ("MonthClaimed", "DayOfWeekClaimed", "WeekOfMonthClaimed", "Year"):
    print(f"  {k} = {features[k]}")

result = ml_fraud_score(features)
print(f"\nFraud score for the $2,450 collision claim: {result}")
print("(Everything else = training-typical values; only the date moves the score.)")
print("\n--- Blended score (rules + ML) ---")
from app.services.risk import score_risk  # noqa: E402
rule_features = {
    "days_policy_to_claim": 30,
    "past_claims": 0,
    "police_report_filed": True,
    "witness_present": True,
    "address_change_near_claim": False,
    "vehicle_price": 20000,
}
blended = score_risk(rule_features, claim=claim)
print(f"Blended risk: {blended}")
