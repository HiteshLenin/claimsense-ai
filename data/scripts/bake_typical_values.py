"""One-off: bake the training-typical values into fraud_bundle.joblib.

risk.py used to re-read the raw training CSV at request time just to
compute each column's median/mode for filling unmapped claim fields.
That made serving depend on the raw dataset existing on disk, which
broke inside the Docker image. The typical values are part of the
model artifact, so they live in the bundle beside the model, the
threshold and the feature columns. Run once; re-run only if the
training data or the typical-value logic ever changes.
"""
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "raw" / "vehicle_fraud" / "fraud_oracle.csv"
BUNDLE_PATH = ROOT / "data" / "models" / "fraud_bundle.joblib"

df = pd.read_csv(CSV_PATH)
typical = {}
for col in df.columns:
    if col in ("FraudFound_P", "PolicyNumber"):
        continue
    if pd.api.types.is_numeric_dtype(df[col]):
        typical[col] = float(df[col].median())
    else:
        typical[col] = df[col].mode().iloc[0]

bundle = joblib.load(BUNDLE_PATH)
bundle["typical_values"] = typical
joblib.dump(bundle, BUNDLE_PATH)
print(f"Baked {len(typical)} typical values into {BUNDLE_PATH}")
