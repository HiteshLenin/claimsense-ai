"""Train a fraud classifier on the Kaggle vehicle-claim fraud dataset.

Run from the project root:
    python data/scripts/train_fraud.py
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# 1. Find the CSV -----------------------------------------------------------
csv_files = list(Path("data/raw/vehicle_fraud").glob("*.csv"))
if not csv_files:
    raise SystemExit("No CSV found in data/raw/vehicle_fraud/")
csv_path = csv_files[0]
print(f"Loading {csv_path} ...")
df = pd.read_csv(csv_path)
print(f"Rows: {len(df)}, columns: {len(df.columns)}")

# 2. Target + features ------------------------------------------------------
TARGET = "FraudFound_P"          # 1 = fraud, 0 = legit
ID_COLS = ["PolicyNumber"]       # identifiers carry no signal; drop them

print("\nFraud rate in data:")
print(df[TARGET].value_counts(normalize=True).round(4))

X = df.drop(columns=[TARGET] + [c for c in ID_COLS if c in df.columns])
y = df[TARGET]

# Models need numbers: one-hot encode every text column into 0/1 columns.
X = pd.get_dummies(X, drop_first=True)
print(f"Feature columns after encoding: {X.shape[1]}")

# 3. Train/test split -------------------------------------------------------
# stratify keeps the ~6% fraud ratio identical in both halves.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train)} rows, test: {len(X_test)} rows")

# 4. Train ------------------------------------------------------------------
# class_weight="balanced" makes fraud mistakes cost ~16x more, so the model
# can't cheat by always predicting "not fraud".
model = RandomForestClassifier(
    n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

# 5. Evaluate on claims the model has NEVER seen -----------------------------
pred = model.predict(X_test)
print("\nConfusion matrix  [rows = actual, cols = predicted]")
print(confusion_matrix(y_test, pred))
print("\nClassification report:")
print(classification_report(y_test, pred, digits=3))

# 6. Save the model ----------------------------------------------------------
out = Path("data/models/fraud_rf.joblib")
out.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, out)
print(f"\nModel saved to {out}")
# 7. Threshold tuning ---------------------------------------------------------
# The model outputs a FRAUD PROBABILITY per claim. predict() flags fraud only
# at >= 0.5. Sweep lower bars: each row shows what happens if we flag every
# claim whose fraud probability is at least the threshold.
proba = model.predict_proba(X_test)[:, 1]
print("\nThreshold sweep  (lower bar -> catch more fraud, review more alarms)")
print(f"{'threshold':>9} {'precision':>9} {'recall':>9} {'flagged':>8}")
for t in [0.5, 0.4, 0.3, 0.2, 0.15, 0.1]:
    flag = proba >= t
    tp = int(((y_test == 1) & flag).sum())
    fp = int(((y_test == 0) & flag).sum())
    fn = int(((y_test == 1) & ~flag).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0
    rec = tp / (tp + fn) if (tp + fn) else 0
    print(f"{t:>9.2f} {prec:>9.3f} {rec:>9.3f} {flag.sum():>8}")
# 8. Save the serving bundle --------------------------------------------------
# The API will load this file: the model + your chosen 0.20 threshold + the
# exact feature columns it trained on (needed to rebuild the same input later).
bundle = {
    "model": model,
    "threshold": 0.20,
    "feature_columns": list(X.columns),
}
bundle_path = Path("data/models/fraud_bundle.joblib")
joblib.dump(bundle, bundle_path)
print(f"Serving bundle saved to {bundle_path}")

