import struct
import zlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Comment,
    Conversation,
    ConversationMember,
    Follow,
    Like,
    Message,
    Notification,
    Post,
    PostImage,
    Story,
    User,
)
from app.services import apply_hashtags
from app.utils.security import hash_password
from app.utils.time import now_iso


def _tiny_png() -> bytes:
    """1x1 gray PNG (~70 bytes). No external/AI image cost."""
    raw = b"\x00\x80\x80\x80"
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


TINY_PNG = _tiny_png()


def _save_png(subdir: str, name: str) -> str:
    folder = Path(settings.upload_dir) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(TINY_PNG)
    return f"/media/{subdir}/{name}"


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return
    now = now_iso()
    people = [
        ("demo@local.test", "demo", "데모 사용자"),
        ("alice@local.test", "alice", "앨리스"),
        ("bob@local.test", "bob", "밥"),
    ]
    users: list[User] = []
    for email, username, full_name in people:
        avatar = _save_png("avatars", f"{username}.png")
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=hash_password("demo1234"),
            bio="데모 계정입니다",
            website="",
            avatar_url=avatar,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        users.append(user)
    db.flush()
    demo, alice, bob = users

    db.add(Follow(follower_id=demo.id, following_id=alice.id, created_at=now))
    db.add(Follow(follower_id=demo.id, following_id=bob.id, created_at=now))
    db.add(Follow(follower_id=alice.id, following_id=demo.id, created_at=now))

    samples = [
        (alice, "서울 노을 #한국 #노을", "서울"),
        (alice, "주말 커피 #음식", "성수"),
        (bob, "도시의 밤 #한국", "홍대"),
        (bob, "점심 세트 #음식", "이태원"),
        (demo, "클론의 첫 게시물 #한국", ""),
    ]
    posts: list[Post] = []
    for i, (author, caption, location) in enumerate(samples):
        post = Post(
            user_id=author.id,
            caption=caption,
            location=location,
            created_at=now,
            updated_at=now,
        )
        db.add(post)
        db.flush()
        url = _save_png("posts", f"p{i}.png")
        db.add(PostImage(post_id=post.id, url=url, position=0))
        apply_hashtags(db, post, caption)
        posts.append(post)

    db.add(Like(post_id=posts[0].id, user_id=demo.id, created_at=now))
    db.add(Comment(post_id=posts[0].id, user_id=demo.id, body="정말 멋져요!", created_at=now))
    db.add(Comment(post_id=posts[4].id, user_id=alice.id, body="환영해요 @demo", created_at=now))

    db.add(
        Story(
            user_id=alice.id,
            media_url=_save_png("stories", "alice.png"),
            created_at=now,
        )
    )
    seed_messages_if_empty(db)
    seed_explore_and_activity(db)
    db.commit()


def seed_messages_if_empty(db: Session) -> None:
    if db.scalar(select(Conversation.id).limit(1)):
        return
    demo = db.scalar(select(User).where(User.username == "demo"))
    alice = db.scalar(select(User).where(User.username == "alice"))
    bob = db.scalar(select(User).where(User.username == "bob"))
    if not demo or not alice or not bob:
        return
    now = now_iso()

    def make_conv(a: User, b: User, lines: list[tuple[User, str]], unread_for: User | None = None) -> None:
        low, high = (a.id, b.id) if a.id < b.id else (b.id, a.id)
        conv = Conversation(user_low_id=low, user_high_id=high, created_at=now, updated_at=now)
        db.add(conv)
        db.flush()
        mem_a = ConversationMember(conversation_id=conv.id, user_id=a.id, created_at=now)
        mem_b = ConversationMember(conversation_id=conv.id, user_id=b.id, created_at=now)
        db.add_all([mem_a, mem_b])
        db.flush()
        message_ids: list[int] = []
        for sender, body in lines:
            msg = Message(conversation_id=conv.id, sender_id=sender.id, body=body, created_at=now)
            db.add(msg)
            db.flush()
            message_ids.append(msg.id)
        conv.updated_at = now
        if message_ids:
            last_id = message_ids[-1]
            if unread_for:
                unread_mem = mem_a if unread_for.id == a.id else mem_b
                other_mem = mem_b if unread_for.id == a.id else mem_a
                unread_mem.last_read_message_id = message_ids[-2] if len(message_ids) > 1 else None
                other_mem.last_read_message_id = last_id
            else:
                mem_a.last_read_message_id = last_id
                mem_b.last_read_message_id = last_id

    make_conv(
        demo,
        alice,
        [
            (alice, "안녕, 피드에 올린 노을 사진 봤어?"),
            (demo, "응, 색감이 정말 좋더라."),
            (alice, "성수에서 찍은 거야. 주말에 카페 갈래?"),
            (demo, "좋아. 토요일 오후 괜찮아?"),
            (alice, "응! 2시에 성수역 앞에서 만나자."),
            (demo, "알겠어. 짧은 메시지도 보여주려고 보냄."),
            (
                alice,
                "긴 메시지 검수용이야. 말풍선이 여러 줄로 잘 접히는지, 목록에는 마지막 문장이 잘리는지 확인해 줘. 위치는 성수, 메뉴는 아메리카노로 부탁해!",
            ),
        ],
        unread_for=demo,
    )
    make_conv(
        demo,
        bob,
        [
            (bob, "점심 메뉴 추천 있어?"),
            (demo, "이태원 쪽 세트 메뉴 괜찮았어."),
            (bob, "오키, 내일 가볼게."),
        ],
    )
    db.commit()


def _ensure_user(db: Session, email: str, username: str, full_name: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user:
        return user
    now = now_iso()
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        password_hash=hash_password("demo1234"),
        bio="데모 계정입니다",
        website="",
        avatar_url=_save_png("avatars", f"{username}.png"),
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()
    return user


def seed_explore_and_activity(db: Session) -> None:
    demo = db.scalar(select(User).where(User.username == "demo"))
    alice = db.scalar(select(User).where(User.username == "alice"))
    bob = db.scalar(select(User).where(User.username == "bob"))
    if not demo:
        return
    now = now_iso()
    cara = _ensure_user(db, "cara@local.test", "cara", "카라")
    dan = _ensure_user(db, "dan@local.test", "dan", "단")

    extra = [
        (cara, "한강 산책 #한국", "여의도", "p-explore-1.png"),
        (dan, "야시장 간식 #음식", "동대문", "p-explore-2.png"),
    ]
    for author, caption, location, filename in extra:
        exists = db.scalar(select(Post).where(Post.user_id == author.id).limit(1))
        if exists:
            continue
        post = Post(
            user_id=author.id,
            caption=caption,
            location=location,
            created_at=now,
            updated_at=now,
        )
        db.add(post)
        db.flush()
        db.add(PostImage(post_id=post.id, url=_save_png("posts", filename), position=0))
        apply_hashtags(db, post, caption)

    demo_post = db.scalar(select(Post).where(Post.user_id == demo.id).order_by(Post.id.asc()))
    wanted = [
        (alice, "like", demo_post.id if demo_post else None, None),
        (bob, "comment", demo_post.id if demo_post else None, "사진 잘 나왔다!"),
        (cara, "follow", None, None),
        (dan, "mention", demo_post.id if demo_post else None, "@demo 여기 봐"),
        (cara, "like", demo_post.id if demo_post else None, None),
    ]
    for actor, ntype, post_id, preview in wanted:
        if not actor:
            continue
        if ntype != "follow" and not post_id:
            continue
        if ntype == "comment" and not preview:
            continue
        exists = db.scalar(
            select(Notification.id).where(
                Notification.user_id == demo.id,
                Notification.actor_id == actor.id,
                Notification.type == ntype,
            )
        )
        if exists:
            continue
        db.add(
            Notification(
                user_id=demo.id,
                actor_id=actor.id,
                type=ntype,
                post_id=post_id,
                comment_preview=preview if ntype in ("comment", "mention") else None,
                read=0,
                created_at=now,
            )
        )
    db.commit()


def ensure_demo_alice_unread(db: Session) -> None:
    """검수용: demo→alice 스레드에 alice 쪽 미읽음 1건이 있도록 last_read를 맞춘다."""
    demo = db.scalar(select(User).where(User.username == "demo"))
    alice = db.scalar(select(User).where(User.username == "alice"))
    if not demo or not alice:
        return
    low, high = sorted([demo.id, alice.id])
    conv = db.scalar(
        select(Conversation).where(Conversation.user_low_id == low, Conversation.user_high_id == high)
    )
    if not conv:
        return
    demo_mem = db.get(ConversationMember, (conv.id, demo.id))
    if not demo_mem:
        return
    last_alice = db.scalar(
        select(Message)
        .where(Message.conversation_id == conv.id, Message.sender_id == alice.id)
        .order_by(Message.id.desc())
        .limit(1)
    )
    if not last_alice:
        return
    prev_id = db.scalar(
        select(Message.id)
        .where(Message.conversation_id == conv.id, Message.id < last_alice.id)
        .order_by(Message.id.desc())
        .limit(1)
    )
    if demo_mem.last_read_message_id != prev_id:
        demo_mem.last_read_message_id = prev_id
        db.commit()


def ensure_admin_user(db: Session) -> None:
    now = now_iso()
    admin = db.scalar(select(User).where(User.username == "admin"))
    if admin:
        admin.is_admin = 1
        admin.password_hash = hash_password("pass123")
        admin.updated_at = now
        db.commit()
        return
    db.add(
        User(
            email="admin@local.test",
            username="admin",
            full_name="관리자",
            password_hash=hash_password("pass123"),
            bio="",
            website="",
            avatar_url=None,
            is_admin=1,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
