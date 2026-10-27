"""Document upload pipeline (SDD: POST /claims/{id}/documents).

v1: validate, checksum, dedupe, store on local disk, save Document row.
Extraction (text per page -> ExtractedFact rows) is the next step;
Azure Blob Storage replaces local disk at Azure deploy time.
"""
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/claims", tags=["documents"])

ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}
MAX_BYTES = 25 * 1024 * 1024
STORAGE = Path(__file__).resolve().parents[3] / "data" / "uploads"


@router.post("/{claim_id}/documents", status_code=201)
def upload_document(claim_id: str, file: UploadFile = File(...),
                    db: Session = Depends(get_db)):
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(404, "claim not found")
    if file.content_type not in ALLOWED:
        raise HTTPException(400, f"unsupported file type: {file.content_type} (pdf/png/jpg only)")

    data = file.file.read()
    if not data:
        raise HTTPException(400, "empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "file too large (max 25MB)")

    checksum = hashlib.sha256(data).hexdigest()
    dup = db.query(models.Document).filter(
        models.Document.checksum_sha256 == checksum).first()
    if dup:
        raise HTTPException(409, "exact duplicate of an already-uploaded document")

    dest_dir = STORAGE / str(claim.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{checksum}{ALLOWED[file.content_type]}"
    dest.write_bytes(data)

    doc = models.Document(
        claim_id=claim.id,
        filename=file.filename or "upload",
        doc_type="other",  # classified at extraction time
        size_bytes=len(data),
        checksum_sha256=checksum,
        s3_key=str(dest),  # local path for now; Blob key at Azure deploy
        extraction_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.add(models.AuditEvent(actor="adjuster-1", action="document.uploaded",
                             entity="document", entity_id=str(doc.id),
                             claim_version=claim.version))
    db.commit()
    return {"id": str(doc.id), "filename": doc.filename,
            "size_bytes": doc.size_bytes,
            "extraction_status": doc.extraction_status}


@router.get("/{claim_id}/documents")
def list_documents(claim_id: str, db: Session = Depends(get_db)):
    docs = db.query(models.Document).filter(
        models.Document.claim_id == claim_id).all()
    return [{"id": str(d.id), "filename": d.filename, "doc_type": d.doc_type,
             "size_bytes": d.size_bytes,
             "extraction_status": d.extraction_status,
             "created_at": d.created_at.isoformat()} for d in docs]
