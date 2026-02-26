from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, EmailConnection, StreamingAccount, SharedAccess
from app.schemas import StreamingAccountCreate, StreamingAccountResponse

router = APIRouter(prefix="/v1/streaming-accounts", tags=["streaming-accounts"])


@router.post("", status_code=201, response_model=StreamingAccountResponse)
def create_streaming_account(
    payload: StreamingAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = db.query(EmailConnection).filter(
        EmailConnection.id == payload.email_connection_id,
        EmailConnection.user_id == current_user.id,
    ).first()
    if conn is None:
        raise HTTPException(status_code=404, detail="email_connection_not_found")

    account = StreamingAccount(
        user_id=current_user.id,
        email_connection_id=conn.id,
        service_name=payload.service_name,
        account_label=payload.account_label,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[StreamingAccountResponse])
def list_streaming_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owned = db.query(StreamingAccount).filter(
        StreamingAccount.user_id == current_user.id,
    ).all()

    shared_ids = db.query(SharedAccess.streaming_account_id).filter(
        SharedAccess.grantee_id == current_user.id,
        SharedAccess.revoked_at.is_(None),
    ).scalar_subquery()

    shared = db.query(StreamingAccount).filter(
        StreamingAccount.id.in_(shared_ids),
    ).all()

    seen = {a.id for a in owned}
    result = list(owned)
    for a in shared:
        if a.id not in seen:
            result.append(a)
    return result
