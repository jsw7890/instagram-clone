from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def _fk_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(full_name)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_nocase ON users(username COLLATE NOCASE)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_nocase ON users(email COLLATE NOCASE)",
    "CREATE INDEX IF NOT EXISTS idx_posts_user_created ON posts(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_saved_posts_user ON saved_posts(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id)",
    "CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_hashtags_name_nocase ON hashtags(name COLLATE NOCASE)",
    "CREATE INDEX IF NOT EXISTS idx_post_hashtags_hashtag ON post_hashtags(hashtag_id)",
    "CREATE INDEX IF NOT EXISTS idx_stories_user ON stories(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_conversation_members_user ON conversation_members(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read)",
)

TRIGGER_STATEMENTS = (
    """
    CREATE TRIGGER trg_members_pair_ins
    BEFORE INSERT ON conversation_members
    FOR EACH ROW
    WHEN NEW.user_id NOT IN (
        SELECT user_low_id FROM conversations WHERE id = NEW.conversation_id
        UNION
        SELECT user_high_id FROM conversations WHERE id = NEW.conversation_id
    )
    OR (
        SELECT COUNT(*) FROM conversation_members WHERE conversation_id = NEW.conversation_id
    ) >= 2
    BEGIN
        SELECT RAISE(ABORT, 'conversation members must be the unique pair');
    END
    """,
    """
    CREATE TRIGGER trg_members_read_ins
    BEFORE INSERT ON conversation_members
    FOR EACH ROW
    WHEN NEW.last_read_message_id IS NOT NULL
     AND NOT EXISTS (
        SELECT 1 FROM messages
        WHERE id = NEW.last_read_message_id AND conversation_id = NEW.conversation_id
     )
    BEGIN
        SELECT RAISE(ABORT, 'last_read_message_id must reference a message in the same conversation');
    END
    """,
    """
    CREATE TRIGGER trg_members_read_upd
    BEFORE UPDATE OF last_read_message_id ON conversation_members
    FOR EACH ROW
    WHEN NEW.last_read_message_id IS NOT NULL
     AND NOT EXISTS (
        SELECT 1 FROM messages
        WHERE id = NEW.last_read_message_id AND conversation_id = NEW.conversation_id
     )
    BEGIN
        SELECT RAISE(ABORT, 'last_read_message_id must reference a message in the same conversation');
    END
    """,
    """
    CREATE TRIGGER trg_messages_sender_ins
    BEFORE INSERT ON messages
    FOR EACH ROW
    WHEN NOT EXISTS (
        SELECT 1 FROM conversation_members
        WHERE conversation_id = NEW.conversation_id AND user_id = NEW.sender_id
    )
    BEGIN
        SELECT RAISE(ABORT, 'sender must be a conversation member');
    END
    """,
    """
    CREATE TRIGGER trg_messages_sender_upd
    BEFORE UPDATE OF sender_id ON messages
    FOR EACH ROW
    WHEN NOT EXISTS (
        SELECT 1 FROM conversation_members
        WHERE conversation_id = NEW.conversation_id AND user_id = NEW.sender_id
    )
    BEGIN
        SELECT RAISE(ABORT, 'sender must be a conversation member');
    END
    """,
)


def _table_sql(conn, name: str) -> str:
    return conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = :name"),
        {"name": name},
    ).scalar() or ""


def _rebuild(conn, name: str, create_sql: str, insert_sql: str) -> None:
    conn.execute(text(f"DROP TABLE IF EXISTS {name}_new"))
    conn.execute(text(create_sql))
    conn.execute(text(insert_sql))
    src = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
    dst = conn.execute(text(f"SELECT COUNT(*) FROM {name}_new")).scalar()
    if src != dst:
        raise RuntimeError(f"{name} rebuild row count {src} != {dst}")
    conn.execute(text(f"DROP TABLE {name}"))
    conn.execute(text(f"ALTER TABLE {name}_new RENAME TO {name}"))


def _migrate(conn) -> None:
    cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
    if cols and "is_private" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_private INTEGER NOT NULL DEFAULT 0"))
    if cols and "show_activity_status" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN show_activity_status INTEGER NOT NULL DEFAULT 1"))
    if cols and "is_admin" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"))

    if cols:
        conn.execute(
            text(
                """
                DELETE FROM notifications
                WHERE actor_id = user_id
                   OR "read" NOT IN (0, 1)
                   OR type NOT IN ('follow', 'like', 'comment', 'mention')
                   OR (
                        type = 'follow'
                        AND (post_id IS NOT NULL OR comment_id IS NOT NULL OR comment_preview IS NOT NULL)
                   )
                   OR (
                        type = 'like'
                        AND (post_id IS NULL OR comment_id IS NOT NULL OR comment_preview IS NOT NULL)
                   )
                   OR (
                        type = 'comment'
                        AND (post_id IS NULL OR comment_preview IS NULL OR length(comment_preview) = 0)
                   )
                   OR (type = 'mention' AND post_id IS NULL)
                """
            )
        )

    users_sql = _table_sql(conn, "users")
    if users_sql and "ck_users_username_lower" not in users_sql:
        _rebuild(
            conn,
            "users",
            """
            CREATE TABLE users_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                bio TEXT NOT NULL,
                website TEXT NOT NULL,
                avatar_url TEXT,
                is_private INTEGER NOT NULL DEFAULT 0,
                show_activity_status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (email),
                UNIQUE (username),
                CONSTRAINT ck_users_is_private CHECK (is_private IN (0, 1)),
                CONSTRAINT ck_users_activity CHECK (show_activity_status IN (0, 1)),
                CONSTRAINT ck_users_username_lower CHECK (username = lower(username)),
                CONSTRAINT ck_users_email_lower CHECK (email = lower(email))
            )
            """,
            """
            INSERT INTO users_new (
                id, email, username, full_name, password_hash, bio, website, avatar_url,
                is_private, show_activity_status, created_at, updated_at
            )
            SELECT
                id, email, username, full_name, password_hash, bio, website, avatar_url,
                is_private, show_activity_status, created_at, updated_at
            FROM users
            """,
        )

    conv_sql = _table_sql(conn, "conversations")
    if conv_sql and "ck_conversations_pair" not in conv_sql:
        _rebuild(
            conn,
            "conversations",
            """
            CREATE TABLE conversations_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_low_id INTEGER NOT NULL,
                user_high_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT uq_conversations_pair UNIQUE (user_low_id, user_high_id),
                CONSTRAINT ck_conversations_pair CHECK (user_low_id < user_high_id),
                FOREIGN KEY(user_low_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(user_high_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """,
            """
            INSERT INTO conversations_new (id, user_low_id, user_high_id, created_at, updated_at)
            SELECT c.id, MIN(cm.user_id), MAX(cm.user_id), c.created_at, c.updated_at
            FROM conversations c
            JOIN conversation_members cm ON cm.conversation_id = c.id
            GROUP BY c.id
            HAVING COUNT(DISTINCT cm.user_id) = 2
            """,
        )

    member_fks = conn.execute(text("PRAGMA foreign_key_list(conversation_members)")).fetchall()
    has_read_fk = any(row[3] == "last_read_message_id" for row in member_fks)
    if _table_sql(conn, "conversation_members") and not has_read_fk:
        _rebuild(
            conn,
            "conversation_members",
            """
            CREATE TABLE conversation_members_new (
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                last_read_message_id INTEGER,
                created_at TEXT NOT NULL,
                PRIMARY KEY (conversation_id, user_id),
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(last_read_message_id) REFERENCES messages(id) ON DELETE SET NULL
            )
            """,
            """
            INSERT INTO conversation_members_new (
                conversation_id, user_id, last_read_message_id, created_at
            )
            SELECT conversation_id, user_id, last_read_message_id, created_at
            FROM conversation_members
            """,
        )

    notif_sql = _table_sql(conn, "notifications")
    if notif_sql and "ck_notifications_shape" not in notif_sql:
        _rebuild(
            conn,
            "notifications",
            """
            CREATE TABLE notifications_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                actor_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                post_id INTEGER,
                comment_id INTEGER,
                comment_preview TEXT,
                "read" INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                CONSTRAINT ck_notifications_type CHECK (type IN ('follow', 'like', 'comment', 'mention')),
                CONSTRAINT ck_notifications_read CHECK ("read" IN (0, 1)),
                CONSTRAINT ck_notifications_not_self CHECK (actor_id != user_id),
                CONSTRAINT ck_notifications_shape CHECK (
                    (type = 'follow' AND post_id IS NULL AND comment_id IS NULL AND comment_preview IS NULL)
                    OR (type = 'like' AND post_id IS NOT NULL AND comment_id IS NULL AND comment_preview IS NULL)
                    OR (
                        type = 'comment' AND post_id IS NOT NULL AND comment_preview IS NOT NULL
                        AND length(comment_preview) > 0
                    )
                    OR (type = 'mention' AND post_id IS NOT NULL)
                ),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(actor_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY(comment_id) REFERENCES comments(id) ON DELETE CASCADE
            )
            """,
            """
            INSERT INTO notifications_new (
                id, user_id, actor_id, type, post_id, comment_id, comment_preview, "read", created_at
            )
            SELECT id, user_id, actor_id, type, post_id, comment_id, comment_preview, "read", created_at
            FROM notifications
            """,
        )

    for stmt in INDEX_STATEMENTS:
        conn.execute(text(stmt))
    for name in (
        "trg_members_pair_ins",
        "trg_members_read_ins",
        "trg_members_read_upd",
        "trg_messages_sender_ins",
        "trg_messages_sender_upd",
    ):
        conn.execute(text(f"DROP TRIGGER IF EXISTS {name}"))
    for stmt in TRIGGER_STATEMENTS:
        conn.execute(text(stmt))


SCHEMA_VERSION = 1


def _ensure_schema_migrations_table(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER NOT NULL PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
    )


def _record_schema_version(conn, version: int) -> None:
    from app.utils.time import now_iso

    conn.execute(
        text(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (:version, :applied_at)
            ON CONFLICT(version) DO UPDATE SET applied_at = excluded.applied_at
            """
        ),
        {"version": version, "applied_at": now_iso()},
    )


def run_migrations() -> None:
    """Apply SQLite schema upgrades (idempotent). Safe to call on every app start."""
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            _ensure_schema_migrations_table(conn)
            _migrate(conn)
            _record_schema_version(conn, SCHEMA_VERSION)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.exec_driver_sql("PRAGMA foreign_keys=ON")
            conn.commit()


def ensure_columns() -> None:
    """Backward-compatible alias."""
    run_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
