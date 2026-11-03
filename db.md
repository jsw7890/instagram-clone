# 데이터베이스 설계 명세서 (SQLite)

저장소는 단일 SQLite 파일 `instagram.db`이다. ORM은 SQLAlchemy 2.x이며, 아래 DDL이 소스 오브 트루스다.

## 1. 원칙

- PK: `INTEGER PRIMARY KEY AUTOINCREMENT`
- 시각: UTC ISO, 컬럼 타입 `TEXT`에 ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- 논리 삭제 없음. 게시물/댓글/스토리는 물리 삭제
- 비밀번호는 bcrypt 해시만 저장
- FK는 `ON DELETE CASCADE`를 기본으로 하여 고아 행을 남기지 않는다
- SQLite에서 `PRAGMA foreign_keys = ON` 필수 (`database.py` 연결 이벤트)

## 2. ER 개요

```mermaid
erDiagram
  users ||--o{ posts : writes
  users ||--o{ comments : writes
  users ||--o{ likes : gives
  users ||--o{ follows : follower
  users ||--o{ follows : following
  users ||--o{ stories : posts
  users ||--o{ saved_posts : saves
  users ||--o{ notifications : receives
  posts ||--|{ post_images : has
  posts ||--o{ comments : has
  posts ||--o{ likes : has
  posts ||--o{ post_hashtags : tagged
  hashtags ||--o{ post_hashtags : used
  stories ||--o{ story_views : seen
  conversations ||--|{ conversation_members : has
  conversations ||--o{ messages : has
  users ||--o{ messages : sends
```

## 3. 테이블

### 3.1 `users`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| email | TEXT | NOT NULL, UNIQUE | 소문자 저장 |
| username | TEXT | NOT NULL, UNIQUE | 소문자, 1~30 |
| full_name | TEXT | NOT NULL DEFAULT `''` | |
| password_hash | TEXT | NOT NULL | |
| bio | TEXT | DEFAULT `''` | 최대 150은 앱 계층 |
| website | TEXT | DEFAULT `''` | |
| avatar_url | TEXT | NULL | `/media/avatars/...` |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

인덱스: UNIQUE(email), UNIQUE(username). 검색용 `username`, `full_name`.

### 3.2 `posts`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| caption | TEXT | DEFAULT `''` | |
| location | TEXT | DEFAULT `''` | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

인덱스: `(user_id, created_at DESC)`, `(created_at DESC)` 피드/탐색.

### 3.3 `post_images`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| post_id | INTEGER | NOT NULL, FK posts.id CASCADE | |
| url | TEXT | NOT NULL | |
| position | INTEGER | NOT NULL DEFAULT 0 | 0부터 |

UNIQUE `(post_id, position)`.

### 3.4 `comments`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| post_id | INTEGER | NOT NULL, FK posts.id CASCADE | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| body | TEXT | NOT NULL | |
| created_at | TEXT | NOT NULL | |

인덱스: `(post_id, created_at)`.

### 3.5 `likes`

게시물 좋아요. 댓글 좋아요는 1차 범위 밖.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| post_id | INTEGER | NOT NULL, FK posts.id CASCADE | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| created_at | TEXT | NOT NULL | |

UNIQUE `(post_id, user_id)`.

### 3.6 `saved_posts`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| post_id | INTEGER | NOT NULL, FK posts.id CASCADE | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| created_at | TEXT | NOT NULL | |

UNIQUE `(post_id, user_id)`.

### 3.7 `follows`

`follower_id`가 `following_id`를 팔로우한다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| follower_id | INTEGER | NOT NULL, FK users.id CASCADE | 나 |
| following_id | INTEGER | NOT NULL, FK users.id CASCADE | 상대 |
| created_at | TEXT | NOT NULL | |

UNIQUE `(follower_id, following_id)`.  
CHECK `follower_id != following_id`.

인덱스: `(following_id)` 팔로워 목록, `(follower_id)` 팔로잉 목록·피드 조인.

### 3.8 `hashtags`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | TEXT | NOT NULL UNIQUE | 소문자, `#` 제외 |
| created_at | TEXT | NOT NULL | |

### 3.9 `post_hashtags`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| post_id | INTEGER | NOT NULL, FK posts.id CASCADE | |
| hashtag_id | INTEGER | NOT NULL, FK hashtags.id CASCADE | |

PK `(post_id, hashtag_id)`.

### 3.10 `stories`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| media_url | TEXT | NOT NULL | |
| created_at | TEXT | NOT NULL | |

만료는 컬럼 없이 `created_at + 24시간`으로 계산한다.  
인덱스: `(user_id, created_at DESC)`.

### 3.11 `story_views`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| story_id | INTEGER | NOT NULL, FK stories.id CASCADE | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| created_at | TEXT | NOT NULL | |

PK `(story_id, user_id)`.

### 3.12 `conversations`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | 마지막 메시지 시각 |

1:1만 지원. 멤버 테이블로 참가자를 표현한다.

### 3.13 `conversation_members`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| conversation_id | INTEGER | NOT NULL, FK conversations.id CASCADE | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| last_read_message_id | INTEGER | NULL, FK messages.id SET NULL | |
| created_at | TEXT | NOT NULL | |

PK `(conversation_id, user_id)`.

두 유저 조합의 유니크는 애플리케이션에서 보장한다. (SQLite에서 쌍 유니크를 내려면 생성 시 `user_id` 정렬 후 기존 대화 조회.)

### 3.14 `messages`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| conversation_id | INTEGER | NOT NULL, FK conversations.id CASCADE | |
| sender_id | INTEGER | NOT NULL, FK users.id CASCADE | |
| body | TEXT | NOT NULL | |
| created_at | TEXT | NOT NULL | |

인덱스: `(conversation_id, id)`.  
이미지 메시지는 1차 범위 밖(텍스트만).

### 3.15 `notifications`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | |
| user_id | INTEGER | NOT NULL, FK users.id CASCADE | 수신자 |
| actor_id | INTEGER | NOT NULL, FK users.id CASCADE | 행위자 |
| type | TEXT | NOT NULL | `follow` `like` `comment` `mention` |
| post_id | INTEGER | NULL, FK posts.id CASCADE | |
| comment_id | INTEGER | NULL, FK comments.id CASCADE | |
| comment_preview | TEXT | NULL | 최대 80자 스냅샷 |
| read | INTEGER | NOT NULL DEFAULT 0 | 0/1 |
| created_at | TEXT | NOT NULL | |

인덱스: `(user_id, created_at DESC)`, `(user_id, read)`.

## 4. DDL

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  username TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  bio TEXT NOT NULL DEFAULT '',
  website TEXT NOT NULL DEFAULT '',
  avatar_url TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  caption TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at DESC);
CREATE INDEX idx_posts_created ON posts(created_at DESC);

CREATE TABLE post_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  UNIQUE(post_id, position)
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_comments_post ON comments(post_id, created_at);

CREATE TABLE likes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  UNIQUE(post_id, user_id)
);

CREATE TABLE saved_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  UNIQUE(post_id, user_id)
);

CREATE TABLE follows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  UNIQUE(follower_id, following_id),
  CHECK(follower_id != following_id)
);
CREATE INDEX idx_follows_following ON follows(following_id);
CREATE INDEX idx_follows_follower ON follows(follower_id);

CREATE TABLE hashtags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE post_hashtags (
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  hashtag_id INTEGER NOT NULL REFERENCES hashtags(id) ON DELETE CASCADE,
  PRIMARY KEY(post_id, hashtag_id)
);

CREATE TABLE stories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  media_url TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_stories_user ON stories(user_id, created_at DESC);

CREATE TABLE story_views (
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  PRIMARY KEY(story_id, user_id)
);

CREATE TABLE conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE conversation_members (
  conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  last_read_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(conversation_id, user_id)
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_messages_conv ON messages(conversation_id, id);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
  comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
  comment_preview TEXT,
  read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
```

`conversation_members.last_read_message_id`가 `messages`를 참조하므로, SQLite에서는 **messages를 먼저 만들고** members를 만드는 편이 안전하다. ORM은 순환 FK를 나중에 `ALTER`하지 말고, `last_read_message_id`를 FK 없이 INTEGER로 두어도 된다. 구현 권장: **FK 없이 INTEGER nullable**로 두고 앱에서 검증.

권장 수정:

```sql
last_read_message_id INTEGER
```

## 5. 주요 쿼리

### 5.1 홈 피드

```sql
SELECT p.*
FROM posts p
WHERE p.user_id = :me
   OR p.user_id IN (SELECT following_id FROM follows WHERE follower_id = :me)
ORDER BY p.created_at DESC, p.id DESC
LIMIT :limit;
```

커서는 `(created_at, id)` 튜플을 base64 JSON으로 인코딩한다.

### 5.2 스토리 피드 (유효)

```sql
SELECT * FROM stories
WHERE created_at >= :cutoff_iso  -- now - 24h
  AND (user_id = :me OR user_id IN (
        SELECT following_id FROM follows WHERE follower_id = :me
      ))
ORDER BY created_at DESC;
```

애플리케이션에서 `user_id`로 그룹핑한다.

### 5.3 미읽음 DM

```sql
SELECT COUNT(*) FROM messages m
WHERE m.conversation_id = :cid
  AND m.sender_id != :me
  AND m.id > COALESCE(:last_read_message_id, 0);
```

### 5.4 해시태그 게시물 수

```sql
SELECT h.name, COUNT(ph.post_id) AS posts_count
FROM hashtags h
LEFT JOIN post_hashtags ph ON ph.hashtag_id = h.id
WHERE h.name LIKE :q || '%'
GROUP BY h.id;
```

## 6. 시드 데이터

| username | email | 관계 |
|----------|-------|------|
| demo | demo@local.test | alice, bob 팔로우 |
| alice | alice@local.test | demo 팔로우 |
| bob | bob@local.test | - |

게시물·이미지는 `backend.md` 시드와 동일. 해시태그 예: `korea`, `food`, `sunset`.

## 7. 백업·운영

- 파일 복사: `instagram.db` (+ WAL 사용 시 `-wal`, `-shm`)
- 업로드 파일은 DB와 별도. 백업 시 `uploads/` 포함
- 동시 쓰기는 SQLite 특성상 제한적. 학습·데모 규모(동시 접속 소수)를 전제로 한다
