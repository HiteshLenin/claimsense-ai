"""Document upload pipeline (SDD: POST /claims/{id}/documents).

v2: validate, checksum, dedupe, store the bytes, save Document row.
Storage destination, chosen by environment:
  - AZURE_STORAGE_CONNECTION_STRING set -> Azure Blob Storage
    (container "claim-documents", blob "<claim_id>/<checksum><ext>")
  - not set -> local disk, data/uploads/ (original v1 behaviour)
Extraction (text per page -> ExtractedFact rows) arrives at Step 9a.
"""
import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/claims", tags=["documents"])

ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}
MAX_BYTES = 25 * 1024 * 1024
STORAGE = Path(__file__).resolve().parents[3] / "data" / "uploads"
BLOB_CONTAINER = "claim-documents"


def _store_bytes(claim_id, checksum, ext, data) -> str:
    """Store the file bytes; return the key saved on the Document row.

    Blob when a connection string is configured, local disk otherwise.
    The blob name mirrors the local layout: <claim_id>/<checksum><ext>.
    """
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        # Imported here so local-only runs never need the Azure SDK.
        from azure.storage.blob import BlobServiceClient

        blob_name = f"{claim_id}/{checksum}{ext}"
        client = BlobServiceClient.from_connection_string(conn_str)
        client.get_blob_client(BLOB_CONTAINER, blob_name).upload_blob(data)
        return blob_name
    dest_dir = STORAGE / str(claim_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{checksum}{ext}"
    dest.write_bytes(data)
    return str(dest)


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

    key = _store_bytes(claim.id, checksum, ALLOWED[file.content_type], data)

    doc = models.Document(
        claim_id=claim.id,
        filename=file.filename or "upload",
        doc_type="other",  # classified at extraction time
        size_bytes=len(data),
        checksum_sha256=checksum,
        s3_key=key,  # Blob name in Azure; local path when disk-backed
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
