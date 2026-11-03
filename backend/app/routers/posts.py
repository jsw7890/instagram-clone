from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Like, Post, PostImage, SavedPost, User
from app.services import (
    apply_hashtags,
    decode_cursor,
    encode_cursor,
    following_ids,
    grid_post,
    notify,
    post_public,
)
from app.utils.media import delete_media, save_upload
from app.utils.time import now_iso

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다")
    return post


@router.post("", status_code=201)
def create_post(
    caption: str = Form(""),
    location: str = Form(""),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not files or len(files) > 10:
        raise HTTPException(status_code=400, detail="이미지는 1장에서 10장까지 올릴 수 있습니다")
    if len(caption) > 2200 or len(location) > 100:
        raise HTTPException(status_code=400, detail="문구 또는 위치가 너무 깁니다")
    now = now_iso()
    post = Post(user_id=current.id, caption=caption, location=location, created_at=now, updated_at=now)
    db.add(post)
    db.flush()
    for i, f in enumerate(files):
        url = save_upload(f, "posts")
        db.add(PostImage(post_id=post.id, url=url, position=i))
    apply_hashtags(db, post, caption)
    db.commit()
    db.refresh(post)
    return post_public(db, post, current)


@router.get("/feed")
def feed(
    cursor: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    q = select(Post)
    if current:
        ids = following_ids(db, current.id) + [current.id]
        q = q.where(Post.user_id.in_(ids))
    decoded = decode_cursor(cursor)
    if decoded:
        t, pid = decoded
        q = q.where((Post.created_at < t) | ((Post.created_at == t) & (Post.id < pid)))
    posts = db.scalars(q.order_by(Post.created_at.desc(), Post.id.desc()).limit(limit + 1)).all()
    next_cursor = None
    if len(posts) > limit:
        posts = posts[:limit]
        next_cursor = encode_cursor(posts[-1].created_at, posts[-1].id)
    return {"items": [post_public(db, p, current) for p in posts], "next_cursor": next_cursor}


@router.get("/explore")
def explore(
    cursor: str | None = None,
    limit: int = Query(18, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    q = select(Post)
    if current:
        q = q.where(Post.user_id != current.id)
        followed = following_ids(db, current.id)
        if followed:
            q = q.where(Post.user_id.not_in(followed))
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


@router.get("/{post_id}")
def get_one(post_id: int, db: Session = Depends(get_db), current: User | None = Depends(get_optional_user)):
    return post_public(db, get_post(db, post_id), current)


@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    post = get_post(db, post_id)
    if post.user_id != current.id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    for img in post.images:
        delete_media(img.url)
    db.delete(post)
    db.commit()
    return {"ok": True}


@router.post("/{post_id}/like")
def like(post_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    post = get_post(db, post_id)
    existing = db.scalar(select(Like).where(Like.post_id == post.id, Like.user_id == current.id))
    if not existing:
        db.add(Like(post_id=post.id, user_id=current.id, created_at=now_iso()))
        notify(db, user_id=post.user_id, actor_id=current.id, ntype="like", post_id=post.id)
        db.commit()
    return {"ok": True}


@router.delete("/{post_id}/like")
def unlike(post_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    post = get_post(db, post_id)
    row = db.scalar(select(Like).where(Like.post_id == post.id, Like.user_id == current.id))
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.post("/{post_id}/save")
def save(post_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    post = get_post(db, post_id)
    existing = db.scalar(select(SavedPost).where(SavedPost.post_id == post.id, SavedPost.user_id == current.id))
    if not existing:
        db.add(SavedPost(post_id=post.id, user_id=current.id, created_at=now_iso()))
        db.commit()
    return {"ok": True}


@router.delete("/{post_id}/save")
def unsave(post_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    post = get_post(db, post_id)
    row = db.scalar(select(SavedPost).where(SavedPost.post_id == post.id, SavedPost.user_id == current.id))
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}
