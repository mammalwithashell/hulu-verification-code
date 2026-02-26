from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.schemas import EmailConnectionCreate

router = APIRouter(prefix="/v1/email-connections", tags=["email-connections"])


@router.post("/test")
def test_email_connection(
    payload: EmailConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate IMAP credentials. Stub: validates shape only. Real IMAP in Phase 5."""
    return {"status": "stub", "message": "Connection test not yet implemented. Credentials shape is valid."}
