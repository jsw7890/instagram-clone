from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Follow, Post, SavedPost, User
from app.schemas import PrivacyOut, PrivacyUpdate, ProfileUpdate
from app.services import (
    decode_cursor,
    encode_cursor,
    following_ids,
    grid_post,
    is_following,
    notify,
    user_public,
)
from app.utils.media import save_upload
from app.utils.time import now_iso

router = APIRouter(prefix="/users", tags=["users"])


def _counts(db: Session, user: User) -> tuple[int, int, int]:
    posts_count = db.scalar(select(func.count()).select_from(Post).where(Post.user_id == user.id)) or 0
    followers = db.scalar(select(func.count()).select_from(Follow).where(Follow.following_id == user.id)) or 0
    following = db.scalar(select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)) or 0
    return posts_count, followers, following


def profile_payload(db: Session, user: User, me: User | None) -> dict:
    posts_count, followers, following = _counts(db, user)
    base = user_public(db, user, me).model_dump()
    base.update(posts_count=posts_count, followers_count=followers, following_count=following)
    if me and me.id == user.id:
        base.update(
            show_activity_status=bool(getattr(user, "show_activity_status", 1)),
            is_admin=bool(getattr(user, "is_admin", 0)),
        )
    return base


def get_user_or_404(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user


@router.get("/suggested")
def suggested(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    posts_count = (
        select(func.count(Post.id)).where(Post.user_id == User.id).correlate(User).scalar_subquery()
    )
    q = select(User).where(User.is_admin == 0)
    if current:
        q = q.where(User.id != current.id)
        following_sub = select(Follow.following_id).where(Follow.follower_id == current.id)
        q = q.where(User.id.not_in(following_sub))
    users = db.scalars(q.order_by(posts_count.desc(), User.id.desc()).limit(limit)).all()
    return [user_public(db, u, current) for u in users]


@router.patch("/me")
def update_me(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if body.full_name is not None:
        current.full_name = body.full_name
    if body.bio is not None:
        current.bio = body.bio
    if body.website is not None:
        current.website = body.website
    current.updated_at = now_iso()
    db.commit()
    db.refresh(current)
    return profile_payload(db, current, current)


@router.get("/me/privacy")
def get_privacy(current: User = Depends(get_current_user)):
    return PrivacyOut(
        is_private=bool(getattr(current, "is_private", 0)),
        show_activity_status=bool(getattr(current, "show_activity_status", 1)),
    )


@router.patch("/me/privacy")
def update_privacy(
    body: PrivacyUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if body.is_private is not None:
        current.is_private = 1 if body.is_private else 0
    if body.show_activity_status is not None:
        current.show_activity_status = 1 if body.show_activity_status else 0
    current.updated_at = now_iso()
    db.commit()
    db.refresh(current)
    return PrivacyOut(
        is_private=bool(current.is_private),
        show_activity_status=bool(current.show_activity_status),
    )


@router.post("/me/avatar")
def avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    current.avatar_url = save_upload(file, "avatars")
    current.updated_at = now_iso()
    db.commit()
    db.refresh(current)
    return profile_payload(db, current, current)


@router.get("/{username}")
def get_user(username: str, db: Session = Depends(get_db), current: User | None = Depends(get_optional_user)):
    user = get_user_or_404(db, username)
    return profile_payload(db, user, current)


@router.get("/{username}/posts")
def user_posts(
    username: str,
    cursor: str | None = None,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    user = get_user_or_404(db, username)
    if getattr(user, "is_private", 0) and (
        not current or (current.id != user.id and not is_following(db, current.id, user.id))
    ):
        return {"items": [], "next_cursor": None}
    q = select(Post).where(Post.user_id == user.id)
    decoded = decode_cursor(cursor)
    if decoded:
        t, pid = decoded
        q = q.where((Post.created_at < t) | ((Post.created_at == t) & (Post.id < pid)))
    posts = db.scalars(q.order_by(Post.created_at.desc(), Post.id.desc()).limit(limit + 1)).all()
    next_cursor = None
    if len(posts) > limit:
        posts = posts[:limit]
        next_cursor = encode_cursor(posts[-1].created_at, posts[-1].id)
    return {"items": [grid_post(db, p) for p in posts], "next_cursor": next_cursor}


@router.get("/{username}/saved")
def saved(
    username: str,
    cursor: str | None = None,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, username)
    if user.id != current.id:
        raise HTTPException(status_code=403, detail="저장한 게시물은 본인만 볼 수 있습니다")
    q = (
        select(Post, SavedPost.created_at)
        .join(SavedPost, SavedPost.post_id == Post.id)
        .where(SavedPost.user_id == current.id)
    )
    decoded = decode_cursor(cursor)
    if decoded:
        t, pid = decoded
        q = q.where((SavedPost.created_at < t) | ((SavedPost.created_at == t) & (Post.id < pid)))
    rows = db.execute(q.order_by(SavedPost.created_at.desc(), Post.id.desc()).limit(limit + 1)).all()
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        saved_at, last_id = rows[-1][1], rows[-1][0].id
        next_cursor = encode_cursor(saved_at, last_id)
    posts = [row[0] for row in rows[:limit]]
    return {"items": [grid_post(db, p) for p in posts], "next_cursor": next_cursor}


@router.post("/{username}/follow")
def follow(username: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    user = get_user_or_404(db, username)
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="자기 자신은 팔로우할 수 없습니다")
    if not is_following(db, current.id, user.id):
        db.add(Follow(follower_id=current.id, following_id=user.id, created_at=now_iso()))
        notify(db, user_id=user.id, actor_id=current.id, ntype="follow")
        db.commit()
    return {"ok": True}


@router.delete("/{username}/follow")
def unfollow(username: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    user = get_user_or_404(db, username)
    row = db.scalar(
        select(Follow).where(Follow.follower_id == current.id, Follow.following_id == user.id)
    )
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.get("/{username}/followers")
def followers(
    username: str,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    user = get_user_or_404(db, username)
    ids = list(db.scalars(select(Follow.follower_id).where(Follow.following_id == user.id)))
    people = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
    return {"items": [user_public(db, u, current) for u in people], "next_cursor": None}


@router.get("/{username}/following")
def following(
    username: str,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    user = get_user_or_404(db, username)
    ids = list(db.scalars(select(Follow.following_id).where(Follow.follower_id == user.id)))
    people = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
    return {"items": [user_public(db, u, current) for u in people], "next_cursor": None}
