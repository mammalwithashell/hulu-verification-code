import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, StreamingAccount, SharedAccess
from app.schemas import SharedAccessCreate, SharedAccessResponse

router = APIRouter(prefix="/v1/shares", tags=["shares"])


@router.post("", status_code=201, response_model=SharedAccessResponse)
def create_share(
    payload: SharedAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(StreamingAccount).filter(
        StreamingAccount.id == payload.streaming_account_id,
        StreamingAccount.user_id == current_user.id,
    ).first()
    if account is None:
        raise HTTPException(status_code=404, detail="streaming_account_not_found")

    grantee = db.query(User).filter(User.id == payload.grantee_id).first()
    if grantee is None:
        raise HTTPException(status_code=404, detail="grantee_not_found")

    share = SharedAccess(
        owner_id=current_user.id,
        grantee_id=payload.grantee_id,
        streaming_account_id=payload.streaming_account_id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


@router.delete("/{share_id}", response_model=SharedAccessResponse)
def revoke_share(
    share_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    share = db.query(SharedAccess).filter(
        SharedAccess.id == share_id,
        SharedAccess.owner_id == current_user.id,
    ).first()
    if share is None:
        raise HTTPException(status_code=404, detail="share_not_found")

    if share.revoked_at is not None:
        raise HTTPException(status_code=400, detail="share_already_revoked")

    share.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(share)
    return share
