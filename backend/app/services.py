import base64
import json
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Comment,
    Follow,
    Hashtag,
    Like,
    Notification,
    Post,
    PostHashtag,
    SavedPost,
    User,
)
from app.schemas import GridPost, ImageOut, PostPublic, UserPublic
from app.utils.time import now_iso

HASHTAG_RE = re.compile(r"#([a-zA-Z0-9가-힣_]{1,50})")
MENTION_RE = re.compile(r"@([a-zA-Z0-9._]{1,30})")


def encode_cursor(created_at: str, item_id: int) -> str:
    raw = json.dumps({"t": created_at, "id": item_id}, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str | None) -> tuple[str, int] | None:
    if not cursor:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return data["t"], int(data["id"])
    except Exception:
        return None


def is_following(db: Session, me_id: int, other_id: int) -> bool:
    if me_id == other_id:
        return False
    return db.scalar(
        select(Follow.id).where(Follow.follower_id == me_id, Follow.following_id == other_id)
    ) is not None


def user_public(db: Session, user: User, me: User | None) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        bio=user.bio or None,
        website=user.website or None,
        is_following=is_following(db, me.id, user.id) if me else False,
        is_me=bool(me) and user.id == me.id,
        is_private=bool(getattr(user, "is_private", 0)),
    )


def following_ids(db: Session, user_id: int) -> list[int]:
    return list(db.scalars(select(Follow.following_id).where(Follow.follower_id == user_id)))


def post_public(db: Session, post: Post, me: User | None) -> PostPublic:
    liked = False
    saved = False
    if me:
        liked = db.scalar(select(Like.id).where(Like.post_id == post.id, Like.user_id == me.id)) is not None
        saved = db.scalar(select(SavedPost.id).where(SavedPost.post_id == post.id, SavedPost.user_id == me.id)) is not None
    likes_count = db.scalar(select(func.count()).select_from(Like).where(Like.post_id == post.id)) or 0
    comments_count = db.scalar(select(func.count()).select_from(Comment).where(Comment.post_id == post.id)) or 0
    return PostPublic(
        id=post.id,
        author=user_public(db, post.author, me),
        caption=post.caption,
        location=post.location,
        images=[ImageOut(id=i.id, url=i.url, position=i.position) for i in post.images],
        likes_count=likes_count,
        comments_count=comments_count,
        liked=liked,
        saved=saved,
        created_at=post.created_at,
    )


def grid_post(db: Session, post: Post) -> GridPost:
    likes_count = db.scalar(select(func.count()).select_from(Like).where(Like.post_id == post.id)) or 0
    comments_count = db.scalar(select(func.count()).select_from(Comment).where(Comment.post_id == post.id)) or 0
    cover = min(post.images, key=lambda i: i.position).url if post.images else None
    return GridPost(
        id=post.id,
        cover_url=cover,
        likes_count=likes_count,
        comments_count=comments_count,
        image_count=len(post.images),
    )


def apply_hashtags(db: Session, post: Post, caption: str) -> None:
    names = {m.group(1).lower() for m in HASHTAG_RE.finditer(caption or "")}
    for name in names:
        tag = db.scalar(select(Hashtag).where(Hashtag.name == name))
        if not tag:
            tag = Hashtag(name=name, created_at=now_iso())
            db.add(tag)
            db.flush()
        db.add(PostHashtag(post_id=post.id, hashtag_id=tag.id))


def notify(
    db: Session,
    *,
    user_id: int,
    actor_id: int,
    ntype: str,
    post_id: int | None = None,
    comment_id: int | None = None,
    comment_preview: str | None = None,
) -> None:
    if user_id == actor_id:
        return
    db.add(
        Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=ntype,
            post_id=post_id,
            comment_id=comment_id,
            comment_preview=(comment_preview[:80] if comment_preview else None),
            read=0,
            created_at=now_iso(),
        )
    )


def mention_users(db: Session, body: str) -> list[User]:
    names = {m.group(1).lower() for m in MENTION_RE.finditer(body or "")}
    if not names:
        return []
    return list(db.scalars(select(User).where(User.username.in_(names))))
