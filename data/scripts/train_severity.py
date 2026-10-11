"""Train the severity classifier (Phase 2).

Same playbook as train_fraud.py: RandomForest on a Kaggle dataset,
stratified split, saved model + serving bundle.

Target: incident_severity — Trivial / Minor / Major / Total Loss.

Run from the project root:
    python data/scripts/train_severity.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

CSV = Path("data/raw/auto_claims/insurance_claims.csv")
OUT_MODEL = Path("data/models/severity_rf.joblib")
OUT_BUNDLE = Path("data/models/severity_bundle.joblib")
TARGET = "incident_severity"


def main():
    df = pd.read_csv(CSV)
    print(f"rows: {len(df)}")
    print("\nTarget distribution:")
    print(df[TARGET].value_counts())

    print("\n_c39 unique values:", df["_c39"].nunique())
    print(df["_c39"].value_counts().head())

    # --- Feature engineering ---
    # Raw dates would explode one-hot (one column per date), so we keep
    # only the incident month. Tenure is already captured by months_as_customer.
    df["incident_month"] = pd.to_datetime(df["incident_date"]).dt.month

    drop = ["policy_number",  # identifier, not signal
            "policy_bind_date", "incident_date",  # raw dates -> incident_month
            "_c39",  # junk column
            "fraud_reported"]  # a future label, not knowable at intake
    df = df.drop(columns=[c for c in drop if c in df.columns])

    # One-hot, but capped: high-cardinality columns (zip, city, car model...)
    # become hundreds of near-empty columns the model memorizes noise from.
    # With 800 training rows, keep only categoricals with few distinct values.
    MAX_CARD = 15
    num_cols = [c for c in df.select_dtypes(include="number").columns if c != TARGET]
    cat_cols = [c for c in df.columns if c not in num_cols + [TARGET]]
    keep_cat = [c for c in cat_cols if df[c].nunique() <= MAX_CARD]
    drop_cat = [c for c in cat_cols if c not in keep_cat]
    print(f"\nKept {len(keep_cat)} categoricals; dropped high-cardinality: {drop_cat}")

    X = pd.concat(
        [df[num_cols].reset_index(drop=True),
         pd.get_dummies(df[keep_cat], drop_first=True).reset_index(drop=True)],
        axis=1,
    )
    y = df[TARGET]
    print(f"Model features after one-hot: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"train: {len(X_train)} | test: {len(X_test)}")

    clf = RandomForestClassifier(n_estimators=200, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    clf.fit(X_train, y_train)

    pred = clf.predict(X_test)
    print("\nConfusion matrix (rows = true, cols = predicted):")
    print(confusion_matrix(y_test, pred, labels=clf.classes_))
    print("\nPer-class precision / recall:")
    print(classification_report(y_test, pred))

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, OUT_MODEL)
    joblib.dump({"model": clf,
                 "feature_columns": list(X.columns),
                 "classes": list(clf.classes_)},
                OUT_BUNDLE)
    print(f"\nSaved {OUT_MODEL} and {OUT_BUNDLE}")


if __name__ == "__main__":
    main()
