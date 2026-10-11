"""First look at our Kaggle datasets. Run from project root: python data/scripts/explore.py"""
from pathlib import Path
import pandas as pd

def load(folder):
    f = next(Path(folder).glob("*.csv"))
    print(f"Loading {f}")
    return pd.read_csv(f)

fraud = load("data/raw/vehicle_fraud")
claims = load("data/raw/auto_claims")

print("\n=== Vehicle fraud dataset ===")
print("Rows x columns:", fraud.shape)
label = [c for c in fraud.columns if "fraud" in c.lower()][0]
print("Fraud column:", label)
print(fraud[label].value_counts(normalize=True).round(3))

print("\n=== Auto claims dataset ===")
print("Rows x columns:", claims.shape)
print("Columns:", list(claims.columns[:12]), "...")
if "incident_severity" in claims.columns:
    print(claims["incident_severity"].value_counts())
