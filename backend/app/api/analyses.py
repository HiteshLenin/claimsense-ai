"""Analysis endpoints (SDD: POST /claims/{id}/analyses, GET /analyses/{id})."""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services import risk, scoring

router = APIRouter(tags=["analyses"])


@router.post("/claims/{claim_id}/analyses")
def start_analysis(claim_id: str, db: Session = Depends(get_db)):
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(404, "claim not found")

    # 1. Severity / priority from transparent rules.
    claim_age_days = (datetime.utcnow() - claim.loss_date).days
    sev = scoring.score_claim(
        amount=claim.amount,
        incident_severity=None,  # not collected at intake yet
        claim_age_days=claim_age_days,
        missing_docs=len(claim.documents) == 0,
    )

    # 2. Fraud risk: rules + ML blend. Only past_claims is truly derivable
    # (other claims under the same policy number); the rest stay neutral
    # until document extraction / richer intake exists.
    past_claims = (
        db.query(models.Claim)
        .filter(models.Claim.policy_number == claim.policy_number,
                models.Claim.id != claim.id)
        .count()
    )
    risk_result = risk.score_risk(
        {
            "days_policy_to_claim": 999,  # unknown -> no signal
            "past_claims": past_claims,
            "police_report_filed": True,  # unknown -> no signal
            "witness_present": True,      # unknown -> no signal
            "address_change_near_claim": False,
            "vehicle_price": 0,
        },
        claim=claim,  # live claim -> ML score via the mapping function
    )

    # 3. Persist one Analysis row (never updated in place) + audit event.
    analysis = models.Analysis(
        claim_id=claim.id,
        claim_version=claim.version,
        severity=sev["severity"],
        priority=sev["priority"],
        risk_score=risk_result["risk_score"],
        risk_reasons=json.dumps([s["code"] for s in risk_result["reasons"]]),
        model_version=risk_result["model_version"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    db.add(models.AuditEvent(actor="system", action="analysis.created",
                             entity="analysis", entity_id=str(analysis.id),
                             claim_version=claim.version))
    db.commit()

    return {
        "id": str(analysis.id),
        "claim_id": str(claim.id),
        "claim_version": claim.version,
        "severity": sev["severity"],
        "priority": sev["priority"],
        "risk_score": risk_result["risk_score"],
        "risk_band": risk_result["risk_band"],
        "risk_reasons": risk_result["reasons"],
        "ml": risk_result["ml"],
        "model_version": risk_result["model_version"],
        "status": analysis.status,
    }


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(404, "analysis not found")
    return {
        "id": str(analysis.id),
        "claim_id": str(analysis.claim_id),
        "claim_version": analysis.claim_version,
        "severity": analysis.severity,
        "priority": analysis.priority,
        "risk_score": analysis.risk_score,
        "risk_reasons": json.loads(analysis.risk_reasons),
        "model_version": analysis.model_version,
        "status": analysis.status,
        "created_at": analysis.created_at.isoformat(),
    }


@router.get("/analyses/{analysis_id}/citations/{chunk_id}")
def get_citation(analysis_id: str, chunk_id: str):
    return {"todo": "return the PolicyChunk source text", "chunk_id": chunk_id}
