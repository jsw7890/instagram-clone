from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, PasswordChangeIn, SignupIn, TokenOut, UserPublic
from app.services import user_public
from app.utils.security import create_access_token, hash_password, verify_password
from app.utils.time import now_iso
from app.routers.users import profile_payload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=201, response_model=TokenOut)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    username = body.username.lower()
    if username == "admin":
        raise HTTPException(status_code=400, detail="사용할 수 없는 사용자 이름입니다")
    exists = db.scalar(select(User).where(or_(User.email == email, User.username == username)))
    if exists:
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일 또는 사용자 이름입니다")
    now = now_iso()
    user = User(
        email=email,
        username=username,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        bio="",
        website="",
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_access_token(user.id, user.username),
        user=UserPublic(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=None,
            is_me=True,
        ),
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    ident = body.username.lower()
    user = db.scalar(select(User).where(or_(User.username == ident, User.email == ident)))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="사용자 이름 또는 비밀번호가 올바르지 않습니다")
    return TokenOut(
        access_token=create_access_token(user.id, user.username),
        user=user_public(db, user, user),
    )


@router.get("/me")
def me(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return profile_payload(db, current, current)


@router.post("/password")
def change_password(
    body: PasswordChangeIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="새 비밀번호는 현재 비밀번호와 달라야 합니다")
    current.password_hash = hash_password(body.new_password)
    current.updated_at = now_iso()
    db.commit()
    return {"ok": True}
