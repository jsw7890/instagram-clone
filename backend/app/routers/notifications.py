from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Notification, User
from app.services import decode_cursor, encode_cursor, user_public

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    cursor: str | None = None,
    limit: int = Query(30, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    q = select(Notification).where(Notification.user_id == current.id)
    decoded = decode_cursor(cursor)
    if decoded:
        t, nid = decoded
        q = q.where((Notification.created_at < t) | ((Notification.created_at == t) & (Notification.id < nid)))
    rows = db.scalars(q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit + 1)).all()
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id)
    unread = db.scalar(
        select(Notification.id).where(Notification.user_id == current.id, Notification.read == 0)
    ) is not None
    return {
        "items": [
            {
                "id": n.id,
                "type": n.type,
                "actor": user_public(db, n.actor, current),
                "post_id": n.post_id,
                "comment_preview": n.comment_preview,
                "read": bool(n.read),
                "created_at": n.created_at,
            }
            for n in rows
        ],
        "next_cursor": next_cursor,
        "has_unread": unread,
    }


@router.post("/read")
def mark_read(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    for n in db.scalars(
        select(Notification).where(Notification.user_id == current.id, Notification.read == 0)
    ).all():
        n.read = 1
    db.commit()
    return {"ok": True}


@router.delete("/{notification_id}")
def delete_one(
    notification_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    row = db.get(Notification, notification_id)
    if not row or row.user_id != current.id:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
    db.delete(row)
    db.commit()
    return {"ok": True}
