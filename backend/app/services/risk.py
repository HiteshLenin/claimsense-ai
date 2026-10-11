"""Fraud-risk indicator (Guide Step 7). ADVISORY ONLY.

Two layers:
  1. Transparent rule signals (always shown with reason codes).
  2. XGBoost model trained on the Kaggle vehicle-claim-fraud dataset
     (saved to models/risk_xgb.joblib) — blended with the rules.

The API must ALWAYS return reason codes alongside the score, so an
adjuster can verify rather than trust.
"""
from functools import lru_cache
from numbers import Number
from pathlib import Path

import pandas as pd

import joblib

RULE_SIGNALS = {
    "claim_within_7d_of_policy_start": 0.25,
    "four_or_more_past_claims": 0.20,
    "no_police_report": 0.15,
    "no_witness": 0.10,
    "address_changed_near_claim": 0.20,
    "high_value_vehicle": 0.10,
}


def rule_signals(features: dict) -> list[dict]:
    """features: dict like {'days_policy_to_claim': 3, 'past_claims': 5, ...}"""
    triggered = []
    checks = {
        "claim_within_7d_of_policy_start": features.get("days_policy_to_claim", 999) <= 7,
        "four_or_more_past_claims": features.get("past_claims", 0) >= 4,
        "no_police_report": not features.get("police_report_filed", True),
        "no_witness": not features.get("witness_present", True),
        "address_changed_near_claim": features.get("address_change_near_claim", False),
        "high_value_vehicle": features.get("vehicle_price", 0) > 69000,
    }
    for code, hit in checks.items():
        if hit:
            triggered.append({"code": code, "weight": RULE_SIGNALS[code]})
    return triggered


def score_risk(features: dict, claim=None) -> dict:
    """Blended fraud-risk score: 50% transparent rules + 50% ML model.

    features: rule inputs, e.g. {'days_policy_to_claim': 3, 'past_claims': 5,
        'police_report_filed': True, 'witness_present': False, ...}
    claim: optional live claim object (needs .loss_date). When given, the
        trained RandomForest scores it via claim_to_model_input().
    """
    signals = rule_signals(features)
    rule_score = min(1.0, sum(s["weight"] for s in signals))

    ml = ml_fraud_score(claim_to_model_input(claim)) if claim is not None else None
    if ml is None:
        final, model_version = rule_score, "rules-v0.1"
    else:
        final = round(0.5 * rule_score + 0.5 * ml["fraud_probability"], 3)
        model_version = "rules-v0.1+rf-v1"

    band = "low" if final < 0.35 else ("medium" if final < 0.65 else "high")
    return {"risk_score": round(final, 3), "risk_band": band,
            "reasons": signals, "ml": ml, "model_version": model_version}

# --- ML fraud model: serving -------------------------------------------------
# Trained 2026-10-01 (see data/scripts/train_fraud.py). The bundle holds the
# model + your 0.20 threshold + the 123 feature columns it expects.

BUNDLE_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "models" / "fraud_bundle.joblib"
)


@lru_cache(maxsize=1)
def _load_bundle():
    if not BUNDLE_PATH.exists():
        return None
    return joblib.load(BUNDLE_PATH)


def ml_fraud_score(kaggle_features: dict) -> dict | None:
    """Score one claim shaped like the Kaggle training rows.

    kaggle_features: raw column names -> values, e.g.
        {"Age": 35, "Sex": "M", "PoliceReportFiled": "Yes", ...}
    Returns {"fraud_probability": 0-1, "flagged": bool},
    or None if the bundle file is missing.
    """
    bundle = _load_bundle()
    if bundle is None:
        return None
    cols = bundle["feature_columns"]
    row = [0.0] * len(cols)
    index = {name: i for i, name in enumerate(cols)}
    for key, value in kaggle_features.items():
        if value != value:  # NaN check: NaN != NaN
            continue
        if key in index and isinstance(value, Number) and not isinstance(value, bool):
            row[index[key]] = float(value)
        elif f"{key}_{value}" in index:
            row[index[f"{key}_{value}"]] = 1.0
    proba = float(bundle["model"].predict_proba([row])[0][1])
    return {
        "fraud_probability": round(proba, 4),
        "flagged": proba >= bundle["threshold"],
    }
# --- Live-claim mapping (Phase 1) -------------------------------------------
# The model speaks Kaggle (33 raw columns -> 123 model columns). A live app
# claim has only a handful of fields. This translator maps what it honestly
# can and fills the rest with training-typical values, so only things the
# app actually knows can move the score.

_CLAIM_CSV = (
    Path(__file__).resolve().parents[3] / "data" / "raw" / "vehicle_fraud" / "fraud_oracle.csv"
)


@lru_cache(maxsize=1)
def _typical_values():
    """Median (numbers) / most common (categories) of each training column."""
    df = pd.read_csv(_CLAIM_CSV)
    typical = {}
    for col in df.columns:
        if col in ("FraudFound_P", "PolicyNumber"):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            typical[col] = float(df[col].median())
        else:
            typical[col] = df[col].mode().iloc[0]
    return typical


def _set_mapped(features, columns, col, value, spellings):
    """Map one live-claim field onto a training column.

    Numeric survivor -> fill the number directly. Exploded one-hot ->
    use the spelling the model was trained on. No match -> keep the
    training-typical value already in features.
    """
    if col in columns:
        features[col] = float(value)
    else:
        for s in spellings:
            if f"{col}_{s}" in columns:
                features[col] = s
                break


def claim_to_model_input(claim) -> dict:
    """Translate a live app claim into a Kaggle-shaped feature dict.

    claim needs .loss_date (a datetime). Feed the result straight
    into ml_fraud_score().
    """
    features = dict(_typical_values())
    bundle = _load_bundle()
    if bundle is None:
        return features
    columns = set(bundle["feature_columns"])
    ld = claim.loss_date
    _set_mapped(features, columns, "MonthClaimed", ld.month,
                [ld.strftime("%b"), ld.strftime("%B"), str(ld.month)])
    _set_mapped(features, columns, "DayOfWeekClaimed", ld.isoweekday(),
                [ld.strftime("%A"), ld.strftime("%a")])
    _set_mapped(features, columns, "WeekOfMonthClaimed", (ld.day - 1) // 7 + 1,
                [str((ld.day - 1) // 7 + 1)])
    _set_mapped(features, columns, "Year", ld.year, [str(ld.year)])
    return features
