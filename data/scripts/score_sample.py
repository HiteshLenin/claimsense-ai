"""Smoke-test: score real Kaggle claims through the backend's risk.py.

Run from the project root:
    python data/scripts/score_sample.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path("backend").resolve()))
from app.services.risk import ml_fraud_score  # noqa: E402

csv = next(Path("data/raw/vehicle_fraud").glob("*.csv"))
df = pd.read_csv(csv)

for label in (1, 0):
    row = df[df["FraudFound_P"] == label].iloc[0]
    result = ml_fraud_score(row.drop("FraudFound_P").to_dict())
    print(f"actual={'FRAUD' if label else 'legit':5} -> {result}")

print("\nIf the FRAUD row got flagged (or a high probability) and the legit")
print("row didn't, your backend is serving your trained model.")
