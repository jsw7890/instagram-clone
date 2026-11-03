from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Comment, Post, User
from app.schemas import CommentIn, CommentOut
from app.services import decode_cursor, encode_cursor, mention_users, notify, user_public
from app.utils.time import now_iso

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: int,
    cursor: str | None = None,
    limit: int = Query(30, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다")
    q = select(Comment).where(Comment.post_id == post_id)
    decoded = decode_cursor(cursor)
    if decoded:
        t, cid = decoded
        q = q.where((Comment.created_at > t) | ((Comment.created_at == t) & (Comment.id > cid)))
    rows = db.scalars(q.order_by(Comment.created_at.asc(), Comment.id.asc()).limit(limit + 1)).all()
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id)
    return {
        "items": [
            CommentOut(
                id=c.id,
                author=user_public(db, c.author, current),
                body=c.body,
                created_at=c.created_at,
            )
            for c in rows
        ],
        "next_cursor": next_cursor,
    }


@router.post("/posts/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int,
    body: CommentIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다")
    comment = Comment(post_id=post.id, user_id=current.id, body=body.body, created_at=now_iso())
    db.add(comment)
    db.flush()
    notify(
        db,
        user_id=post.user_id,
        actor_id=current.id,
        ntype="comment",
        post_id=post.id,
        comment_id=comment.id,
        comment_preview=body.body,
    )
    for mentioned in mention_users(db, body.body):
        if mentioned.id == current.id or mentioned.id == post.user_id:
            continue
        notify(
            db,
            user_id=mentioned.id,
            actor_id=current.id,
            ntype="mention",
            post_id=post.id,
            comment_id=comment.id,
            comment_preview=body.body,
        )
    db.commit()
    db.refresh(comment)
    return CommentOut(
        id=comment.id,
        author=user_public(db, current, current),
        body=comment.body,
        created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
    post = db.get(Post, comment.post_id)
    if comment.user_id != current.id and (not post or post.user_id != current.id):
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    db.delete(comment)
    db.commit()
    return {"ok": True}
