from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_admin_user
from app.models import Comment, Follow, Like, Message, Post, Story, User
from app.utils.media import delete_media
from app.utils.time import now_iso

router = APIRouter(prefix="/admin", tags=["admin"])


def _seven_days_ago_iso() -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(get_admin_user)):
    since = _seven_days_ago_iso()
    recent_users = db.scalars(
        select(User).where(User.is_admin == 0, User.created_at >= since).order_by(User.created_at.desc()).limit(8)
    ).all()
    return {
        "users": db.scalar(select(func.count()).select_from(User).where(User.is_admin == 0)) or 0,
        "posts": db.scalar(select(func.count()).select_from(Post)) or 0,
        "comments": db.scalar(select(func.count()).select_from(Comment)) or 0,
        "likes": db.scalar(select(func.count()).select_from(Like)) or 0,
        "follows": db.scalar(select(func.count()).select_from(Follow)) or 0,
        "messages": db.scalar(select(func.count()).select_from(Message)) or 0,
        "stories": db.scalar(select(func.count()).select_from(Story)) or 0,
        "signups_last_7_days": db.scalar(
            select(func.count()).select_from(User).where(User.is_admin == 0, User.created_at >= since)
        )
        or 0,
        "posts_last_7_days": db.scalar(select(func.count()).select_from(Post).where(Post.created_at >= since)) or 0,
        "recent_signups": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "created_at": u.created_at,
            }
            for u in recent_users
        ],
    }


@router.get("/users")
def list_users(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    query = select(User).where(User.is_admin == 0)
    count_q = select(func.count()).select_from(User).where(User.is_admin == 0)
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        filt = or_(User.username.like(term), User.email.like(term), User.full_name.like(term))
        query = query.where(filt)
        count_q = count_q.where(filt)
    total = db.scalar(count_q) or 0
    rows = db.scalars(query.order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * limit).limit(limit)).all()
    items = []
    for u in rows:
        posts_count = db.scalar(select(func.count()).select_from(Post).where(Post.user_id == u.id)) or 0
        items.append(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "created_at": u.created_at,
                "posts_count": posts_count,
            }
        )
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="관리자 계정은 탈퇴 처리할 수 없습니다")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="본인 계정은 탈퇴 처리할 수 없습니다")
    if user.avatar_url:
        delete_media(user.avatar_url)
    for post in list(user.posts):
        for img in post.images:
            delete_media(img.url)
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.get("/posts")
def list_posts(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    query = select(Post)
    count_q = select(func.count()).select_from(Post)
    if q and q.strip():
        term = f"%{q.strip()}%"
        filt = or_(Post.caption.like(term), Post.location.like(term))
        query = query.where(filt)
        count_q = count_q.where(filt)
    total = db.scalar(count_q) or 0
    posts = db.scalars(query.order_by(Post.created_at.desc(), Post.id.desc()).offset((page - 1) * limit).limit(limit)).all()
    items = []
    for p in posts:
        author = db.get(User, p.user_id)
        likes = db.scalar(select(func.count()).select_from(Like).where(Like.post_id == p.id)) or 0
        comments = db.scalar(select(func.count()).select_from(Comment).where(Comment.post_id == p.id)) or 0
        items.append(
            {
                "id": p.id,
                "author": {
                    "id": author.id if author else p.user_id,
                    "username": author.username if author else "?",
                },
                "caption": p.caption,
                "location": p.location,
                "created_at": p.created_at,
                "likes_count": likes,
                "comments_count": comments,
                "image_count": len(p.images),
                "cover_url": p.images[0].url if p.images else None,
            }
        )
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.delete("/posts/{post_id}")
def delete_post_admin(post_id: int, db: Session = Depends(get_db), _: User = Depends(get_admin_user)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다")
    for img in post.images:
        delete_media(img.url)
    db.delete(post)
    db.commit()
    return {"ok": True}
