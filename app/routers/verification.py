import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, StreamingAccount, SharedAccess, VerificationRequest, VerificationEvent
from app.schemas import VerificationRequestCreate, VerificationResultResponse

router = APIRouter(prefix="/v1/verification", tags=["verification"])


def _user_can_access_account(db: Session, user: User, account_id: uuid.UUID) -> bool:
    account = db.query(StreamingAccount).filter(StreamingAccount.id == account_id).first()
    if account is None:
        return False
    if account.user_id == user.id:
        return True
    share = db.query(SharedAccess).filter(
        SharedAccess.grantee_id == user.id,
        SharedAccess.streaming_account_id == account_id,
        SharedAccess.revoked_at.is_(None),
    ).first()
    return share is not None


@router.post("/request", status_code=201, response_model=VerificationResultResponse)
def create_verification_request(
    payload: VerificationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _user_can_access_account(db, current_user, payload.streaming_account_id):
        raise HTTPException(status_code=404, detail="streaming_account_not_found")

    account = db.query(StreamingAccount).filter(StreamingAccount.id == payload.streaming_account_id).first()

    req = VerificationRequest(
        requester_id=current_user.id,
        streaming_account_id=payload.streaming_account_id,
        status="pending",
    )
    db.add(req)
    db.flush()

    event = VerificationEvent(
        verification_request_id=req.id,
        event_type="requested",
        detail=f"Verification requested by {current_user.email}",
    )
    db.add(event)
    db.commit()
    db.refresh(req)

    return VerificationResultResponse(
        id=req.id,
        streaming_account_id=req.streaming_account_id,
        status=req.status,
        code=req.code,
        source_service=account.service_name,
        received_at=req.completed_at,
        confidence=req.confidence,
        error=req.error,
    )


@router.get("/{request_id}", response_model=VerificationResultResponse)
def get_verification_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(VerificationRequest).filter(VerificationRequest.id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail="verification_request_not_found")

    account = db.query(StreamingAccount).filter(StreamingAccount.id == req.streaming_account_id).first()
    if req.requester_id != current_user.id and account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="verification_request_not_found")

    return VerificationResultResponse(
        id=req.id,
        streaming_account_id=req.streaming_account_id,
        status=req.status,
        code=req.code,
        source_service=account.service_name,
        received_at=req.completed_at,
        confidence=req.confidence,
        error=req.error,
    )
