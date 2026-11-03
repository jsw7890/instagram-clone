from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.utils.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if not creds:
        return None
    payload = decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        return None
    return db.get(User, int(payload["sub"]))


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    user = get_optional_user(creds, db)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return user


def get_admin_user(current: User = Depends(get_current_user)) -> User:
    if not getattr(current, "is_admin", 0):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return current
