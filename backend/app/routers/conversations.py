from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Conversation, ConversationMember, Message, User
from app.schemas import ConversationCreate, MessageIn
from app.services import decode_cursor, encode_cursor, user_public
from app.utils.time import now_iso

router = APIRouter(prefix="/conversations", tags=["conversations"])


def member_or_403(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    mem = db.get(ConversationMember, (conversation_id, user_id))
    if not mem:
        raise HTTPException(status_code=403, detail="참가자가 아닙니다")
    return conv


def other_user(db: Session, conversation_id: int, me_id: int) -> User | None:
    uid = db.scalar(
        select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id != me_id,
        )
    )
    return db.get(User, uid) if uid else None


def last_message(db: Session, conversation_id: int) -> Message | None:
    return db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(1)
    )


def unread_count(db: Session, conversation_id: int, me_id: int) -> int:
    mem = db.get(ConversationMember, (conversation_id, me_id))
    last_read = mem.last_read_message_id if mem else None
    q = select(func.count()).select_from(Message).where(
        Message.conversation_id == conversation_id,
        Message.sender_id != me_id,
    )
    if last_read:
        q = q.where(Message.id > last_read)
    return db.scalar(q) or 0


def find_or_create(db: Session, a: int, b: int) -> Conversation:
    low, high = (a, b) if a < b else (b, a)
    existing = db.scalar(
        select(Conversation).where(Conversation.user_low_id == low, Conversation.user_high_id == high)
    )
    if existing:
        return existing
    now = now_iso()
    conv = Conversation(user_low_id=low, user_high_id=high, created_at=now, updated_at=now)
    db.add(conv)
    db.flush()
    db.add(ConversationMember(conversation_id=conv.id, user_id=a, created_at=now))
    db.add(ConversationMember(conversation_id=conv.id, user_id=b, created_at=now))
    db.commit()
    db.refresh(conv)
    return conv


def conv_item(db: Session, conv: Conversation, me: User) -> dict:
    other = other_user(db, conv.id, me.id)
    msg = last_message(db, conv.id)
    return {
        "id": conv.id,
        "other_user": user_public(db, other, me) if other else None,
        "last_message": (
            {"id": msg.id, "body": msg.body, "sender_id": msg.sender_id, "created_at": msg.created_at}
            if msg
            else None
        ),
        "unread_count": unread_count(db, conv.id, me.id),
    }


@router.get("")
def list_conversations(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    conv_ids = list(
        db.scalars(select(ConversationMember.conversation_id).where(ConversationMember.user_id == current.id))
    )
    convs = db.scalars(select(Conversation).where(Conversation.id.in_(conv_ids))).all() if conv_ids else []
    convs = sorted(convs, key=lambda c: c.updated_at, reverse=True)
    return [conv_item(db, c, current) for c in convs]


@router.post("")
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    other = db.scalar(select(User).where(User.username == body.username.lower()))
    if not other:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if other.id == current.id:
        raise HTTPException(status_code=400, detail="자기 자신에게는 메시지를 보낼 수 없습니다")
    conv = find_or_create(db, current.id, other.id)
    return conv_item(db, conv, current)


@router.get("/{conversation_id}/messages")
def list_messages(
    conversation_id: int,
    cursor: str | None = None,
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    member_or_403(db, conversation_id, current.id)
    q = select(Message).where(Message.conversation_id == conversation_id)
    decoded = decode_cursor(cursor)
    if decoded:
        _t, mid = decoded
        q = q.where(Message.id < mid)
    rows = db.scalars(q.order_by(Message.id.desc()).limit(limit + 1)).all()
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id)
    rows = list(reversed(rows))
    return {
        "items": [
            {
                "id": m.id,
                "body": m.body,
                "sender_id": m.sender_id,
                "created_at": m.created_at,
            }
            for m in rows
        ],
        "next_cursor": next_cursor,
    }


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    body: MessageIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    conv = member_or_403(db, conversation_id, current.id)
    msg = Message(
        conversation_id=conv.id,
        sender_id=current.id,
        body=body.body,
        created_at=now_iso(),
    )
    conv.updated_at = msg.created_at
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "body": msg.body, "sender_id": msg.sender_id, "created_at": msg.created_at}


@router.post("/{conversation_id}/read")
def mark_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    member_or_403(db, conversation_id, current.id)
    last = db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(1)
    )
    mem = db.get(ConversationMember, (conversation_id, current.id))
    if last and mem:
        mem.last_read_message_id = last.id
        db.commit()
    return {"ok": True}
