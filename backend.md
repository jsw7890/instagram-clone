# 백엔드 개발 명세서 (FastAPI + SQLite)

이 문서는 **현재 프론트엔드(`frontend/src`)가 실제로 그리는 화면과 호출하는 API**만 정의한다.  
스키마는 구현된 SQLite 모델(`backend/app/models.py`)과 같다. `front.md`의 미구현 기능은 범위에서 뺀다.

충돌 시 우선순위: **프론트 화면 → 이 문서 → `db.md`**.

---

## 1. 목표

단일 SQLite 파일로 Instagram 클론 웹의 **표시·조작에 필요한 REST**만 제공한다.

프론트가 쓰는 기능만 구현한다.

- 회원가입 / 로그인 / JWT / 비밀번호 변경
- 게스트 둘러보기(피드·탐색·검색·게시 상세·프로필 읽기)
- 게시(이미지 1~10장), 삭제, 좋아요, 댓글, 저장
- 팔로우, 추천 유저, 팔로워/팔로잉 목록
- 프로필 편집·아바타, 비공개 계정·활동 상태
- 스토리(업로드·피드·조회·삭제, 24시간)
- 1:1 텍스트 DM
- 알림 목록·읽음·**단건 삭제**
- 검색(계정/태그/게시물)
- 시드 데이터(검수용)

### 1.1 하지 않는다

프론트에 화면이 없거나 호출하지 않는 것은 구현하지 않는다.

- PostgreSQL, Redis, Alembic 필수화, 웹소켓
- 릴스, 라이브, 쇼핑, 광고, 영상 업로드
- 그룹 DM, 이미지 메시지, 읽음 영수증 UI
- 알림 **전체 삭제** API/버튼
- 게시물 수정, 댓글 좋아요
- `GET /stories/{id}` (프론트 미사용)

---

## 2. 런타임·환경

개발·프로덕트 **모두 SQLite**다. DB 엔진을 환경별로 바꾸지 않는다.

| 항목 | 값 |
|------|-----|
| 앱 | FastAPI, Python 3.11+ (3.15는 `Mapped[T \| None]` 대신 `Mapped[int]` + `nullable=True`) |
| ORM | SQLAlchemy 2.x, `PRAGMA foreign_keys=ON` |
| 검증 | Pydantic v2 |
| 인증 | JWT HS256, `Authorization: Bearer` |
| 비밀번호 | passlib + bcrypt, 8~72자 |
| 파일 | `uploads/` 디스크, `/media` 정적 서빙 |
| 포트 | `8000` |
| 프리픽스 | `/api` |
| OpenAPI | `/docs` |

마이그레이션: `Base.metadata.create_all` + `run_migrations()` (`ensure_columns`는 동일 alias). 수동 실행: 프로젝트 루트 `npm run db:migrate` 또는 `backend/migrate.py`. 적용 버전은 `schema_migrations` 테이블에 기록된다. 컬럼 추가는 `ALTER TABLE`. SQLite가 기존 테이블에 넣지 못하는 제약(계정 CHECK, 1:1 대화 쌍, 알림 형태, 읽음 FK)은 그 테이블을 다시 만들고 행을 옮긴다. Alembic은 쓰지 않는다.

### 2.1 설정

`.env` 공통. 프로덕트는 `SECRET_KEY`와 `CORS_ORIGINS`만 반드시 바꾼다. `DATABASE_URL`은 양쪽 모두 SQLite다.

| 변수 | 개발 기본 | 프로덕트 |
|------|-----------|----------|
| `SECRET_KEY` | `dev-instagram-clone-change-me` | 강한 임의 문자열 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | 동일 가능 |
| `DATABASE_URL` | `sqlite:///./instagram.db` | `sqlite:////var/data/instagram.db` 등 **파일 경로만 변경** |
| `UPLOAD_DIR` | `uploads` | 쓰기 가능한 디렉터리 |
| `CORS_ORIGINS` | `http://localhost:5173` | 실제 프론트 origin, 콤마 구분 |
| `MAX_UPLOAD_MB` | `10` | 동일 |

SQLite 파일과 `uploads/`를 함께 백업한다. WAL 사용 시 `-wal`, `-shm` 포함.

---

## 3. 프론트 화면 ↔ API

게스트는 토큰 없이 읽기만 한다. 쓰기(만들기·좋아요·댓글·저장·팔로우·스토리·DM·알림·설정)는 로그인. 미인증 쓰기는 `401` `{ "detail": "로그인이 필요합니다" }`.

| 화면 | 경로 | 인증 | 백엔드 |
|------|------|------|--------|
| 로그인 | `/login` | 비로그인 | `POST /auth/login` |
| 가입 | `/signup` | 비로그인 | `POST /auth/signup` |
| 피드 | `/` | 선택 | `GET /posts/feed`, `GET /users/suggested`, 로그인 시 `GET /stories/feed` |
| 탐색 | `/explore` | 선택 | `GET /posts/explore` |
| 검색 | `/search` | 선택 | `GET /search` |
| 게시 상세 | `/p/:postId` | 선택 | `GET /posts/{id}`, `GET /posts/{id}/comments` + 쓰기 API |
| 프로필 | `/:username` | 선택 | `GET /users/{username}`, `GET /users/{username}/posts`, `GET /users/{username}/followers`, `GET /users/{username}/following`, follow, 본인 시 `PATCH /users/me`, `POST /users/me/avatar` |
| 저장됨 | `/:username/saved` | 필수, 본인 | `GET /users/{username}/saved` |
| 만들기 모달 | 사이드바 | 필수 | `POST /posts` |
| DM | `/direct`, `/direct/:id` | 필수 | conversations + messages |
| 알림 | `/activity` | 필수 | `GET /notifications`, `POST /notifications/read`, `DELETE /notifications/{id}` |
| 설정 | `/settings` | 필수 | 메뉴만 (프론트) |
| 비밀번호 | `/settings/password` | 필수 | `POST /auth/password` |
| 개인정보 | `/settings/privacy` | 필수 | `GET`/`PATCH /users/me/privacy` |
| 세션 복구 | 전역 | 토큰 있으면 | `GET /auth/me` |

토큰: `localStorage` 키 `ig_token`. Axios `baseURL` = `VITE_API_BASE_URL` (기본 `http://localhost:8000/api`). 이미지 src = `VITE_API_ORIGIN` + `/media/...`.

---

## 4. 공통 규칙

### 4.1 인증

- 가입 시 username·email은 **소문자 저장**, 유니크
- username: `^[a-zA-Z0-9._]{1,30}$`
- 로그인 `username` 필드에 **사용자명 또는 이메일**
- JWT payload: `{ sub: user_id, username, exp }`
- 선택 인증: `HTTPBearer(auto_error=False)` → `get_optional_user` (없으면 `null`)
- 에러 `detail`은 **한국어** (프론트가 그대로 표시)

### 4.2 페이지네이션

요청 `cursor`, `limit`. 응답 `{ "items": [], "next_cursor": null | string }`.  
커서는 opaque(보통 `created_at`+`id` base64). 프론트는 해석하지 않는다.

피드 `limit=10`, 탐색 `limit=18`, 프로필·저장 그리드 기본 `limit=12`. 댓글·알림·메시지는 프론트가 cursor만 넘기기도 한다.

**예외:** `GET /users/suggested`만 응답이 `UserPublic[]` 배열이다(객체로 감싸지 않음).

### 4.3 미디어

- MIME: jpeg / png / webp, 장당 `MAX_UPLOAD_MB`
- DB에는 `/media/{avatars|posts|stories}/파일명`
- 게시·스토리 삭제 시 파일 삭제 시도

### 4.4 게스트 피드

토큰 없음: **전체 최신 게시물**.  
로그인: 팔로잉 + 본인.

탐색: 로그인 시 본인·팔로잉 제외. 게스트는 전체 최신.

---

## 5. 데이터 (SQLite만)

테이블은 프론트 화면이 읽는 값만 저장한다. 논리 삭제는 없다. 시각은 UTC ISO 문자열(`TEXT`). PK는 정수다. 모델은 `AUTOINCREMENT`를 쓴다. 예전에 만들어진 `posts` 같은 테이블은 `INTEGER PRIMARY KEY`(rowid)라서, 가장 큰 id를 지운 직후의 다음 행이 그 번호를 다시 받을 수 있다. 화면은 id를 그대로 쓴다.

좋아요 수, 댓글 수, 팔로워/팔로잉/게시 수, `liked`, `saved`, `is_following`, `is_me`, `cover_url`, `image_count`, 태그의 `posts_count`, `unread_count`, `has_unseen`, `seen`은 컬럼이 아니다. 조회할 때 계산한다.

불리언은 `INTEGER`이며 **0 또는 1만** 허용한다.

| 테이블 | 화면 | 지키는 것 |
|--------|------|-----------|
| `users` | 로그인, 프로필, 설정 | 이메일·사용자명 소문자, 대소문자 무시 유니크 |
| `posts`, `post_images` | 피드, 탐색, 상세, 작성 | 같은 게시에서 `position` 유니크. 1~10장은 API가 막는다 |
| `comments` | 상세·카드 댓글 | 대댓글·댓글 좋아요 없음 |
| `likes` | 좋아요 | `(post_id, user_id)` 유니크 |
| `saved_posts` | 저장됨 탭 | `(post_id, user_id)` 유니크. 목록은 `user_id, created_at` |
| `follows` | 팔로우, 피드, 추천 | 자기 자신 금지. 맞팔 요청 테이블 없음 |
| `hashtags`, `post_hashtags` | 검색 태그 | 이름 소문자·`#` 없음. `hashtag_id`로 게시물을 찾음 |
| `stories`, `story_views` | 스토리 바·뷰어 | 만료 컬럼 없음. `created_at + 24h`. 조회는 `(story_id, user_id)` |
| `conversations`, `conversation_members`, `messages` | DM | 두 유저 1스레드. 텍스트만 |
| `notifications` | 알림 | `follow` `like` `comment` `mention`. 단건 DELETE |

### 5.1 컬럼과 제약

`users`: `email`, `username`(소문자, 각각 `COLLATE NOCASE` 유니크), `full_name`, `password_hash`, `bio`, `website`(빈 문자열 기본, NOT NULL), `avatar_url`(NULL 허용), `is_private`(기본 0), `show_activity_status`(기본 1), `created_at`, `updated_at`.

`website`가 빈 문자열이면 API 응답은 `null`이어도 된다. 프론트 편집 폼은 `|| ""`로 받는다. 프로필 헤더는 website를 그리지 않고, 값은 편집 저장용이다.

`show_activity_status`는 설정의 켜짐/꺼짐만 저장한다. 접속 중·마지막 활동 시각 컬럼은 없다. 그 상태를 그리는 화면이 없기 때문이다.

`posts`: `user_id`, `caption`, `location`(둘 다 빈 문자열 허용), `created_at`, `updated_at`. 게시 수정 API는 없다.

`post_images`: `url`, `position`(0부터). 그리드 `cover_url`은 `position`이 가장 작은 이미지다.

`comments`: `post_id`, `user_id`, `body`, `created_at`.

`saved_posts.created_at`은 저장한 시각이다. 저장됨 탭이 사용자 기준으로 읽으므로 `(user_id, created_at DESC)` 인덱스를 둔다.

`follows`: `follower_id`, `following_id`, `created_at`. `follower_id != following_id`. 비공개 계정도 팔로우는 즉시 생기고, 게시물 가시성만 API가 거른다. 팔로우 요청 테이블은 없다.

`hashtags.name`은 `#` 없이 저장한다. `post_hashtags`의 PK는 `(post_id, hashtag_id)`라서 태그→게시 조회용으로 `hashtag_id` 인덱스를 따로 둔다. 같은 이름의 대소문자 변형은 `COLLATE NOCASE` 유니크로 막는다.

`stories`: `user_id`, `media_url`, `created_at`. `story_views`는 누가 봤는지와 `created_at`만 있다.

`conversations`: `user_low_id < user_high_id`, 그 쌍은 유니크. 둘 다 `users.id`이고 유저 삭제 시 대화가 CASCADE된다. 그룹 DM 컬럼은 없다.

`conversation_members`: PK `(conversation_id, user_id)`. 멤버는 그 대화의 `user_low_id`, `user_high_id` 두 명뿐이어야 한다. 목록 조회용 `user_id` 인덱스. `last_read_message_id`는 **같은 대화의** `messages.id`를 가리키고, 그 메시지가 지워지면 NULL이 된다. NULL이면 상대가 보낸 메시지를 아직 안 읽은 것으로 계산한다.

`messages`: `conversation_id`, `sender_id`, `body`, `created_at`. 보낸 사람은 그 대화의 멤버여야 한다. 이미지 메시지 컬럼은 없다.

`notifications`:

| 컬럼 | 규칙 |
|------|------|
| `user_id` | 받는 사람 |
| `actor_id` | 행동한 사람. `user_id`와 같을 수 없다 |
| `type` | `follow`, `like`, `comment`, `mention` |
| `read` | 0 또는 1. 읽음 처리는 행을 지우지 않는다 |
| `post_id` | `follow`는 NULL. `like`/`comment`/`mention`은 필수. 게시 삭제 시 CASCADE |
| `comment_id` | 댓글이 있으면 연결. 댓글 삭제 시 그 알림도 CASCADE. `like`/`follow`는 NULL |
| `comment_preview` | `comment`는 필수(프론트가 이 문장을 보여 줌). `like`/`follow`는 NULL. `mention`은 있어도 된다 |
| `created_at` | 정렬 |

프론트는 `post_id`가 있으면 `/p/{post_id}`로, 없으면 행위자 프로필로 간다. 그래서 게시물이 없는 좋아요·댓글·멘션 행은 저장하지 않는다. 기동 시 그 조건에 안 맞는 기존 행은 지운다. **전체 삭제 API는 두지 않는다.**

비공개 계정: `is_private=1`이면 본인·팔로워가 아닌 요청의 `GET /users/{username}/posts`는 빈 `items`.

---

## 6. API 계약

베이스 `http://localhost:8000/api`. 성공 JSON만 적는다. 필드명은 프론트 `src/api/*`와 동일해야 한다.

### 6.0 검증 요약 (프론트 ↔ 명세 ↔ DB)

프론트 `src/api/*`·각 페이지가 호출하는 엔드포인트 **41개**만 유지한다. 아래 표에 없는 경로는 OpenAPI에 두지 않는다.

| # | 메서드 | 경로 | 인증 | 프론트 | 주 DB |
|---|--------|------|------|--------|--------|
| 1 | POST | `/auth/signup` | — | `auth.signup` | `users` |
| 2 | POST | `/auth/login` | — | `auth.login` | `users` |
| 3 | GET | `/auth/me` | 필수 | `auth.me` | `users`, `posts`, `follows` (카운트) |
| 4 | POST | `/auth/password` | 필수 | `auth.changePassword` | `users.password_hash` |
| 5 | GET | `/users/suggested` | 선택 | `users.suggested` | `users`, `follows` |
| 6 | PATCH | `/users/me` | 필수 | `users.updateMe` | `users` |
| 7 | POST | `/users/me/avatar` | 필수 | `users.uploadAvatar` | `users.avatar_url` |
| 8 | GET | `/users/me/privacy` | 필수 | `users.getPrivacy` | `users.is_private`, `show_activity_status` |
| 9 | PATCH | `/users/me/privacy` | 필수 | `users.updatePrivacy` | 동일 |
| 10 | GET | `/users/{username}` | 선택 | `users.getUser` | `users`, `follows` |
| 11 | GET | `/users/{username}/posts` | 선택 | `users.userPosts` | `posts`, `post_images`, `likes`, `comments` |
| 12 | GET | `/users/{username}/saved` | 필수·본인 | `users.savedPosts` | `saved_posts`, `posts`, `post_images` |
| 13 | POST | `/users/{username}/follow` | 필수 | `users.follow` | `follows`, `notifications` |
| 14 | DELETE | `/users/{username}/follow` | 필수 | `users.unfollow` | `follows` |
| 15 | GET | `/users/{username}/followers` | 선택 | `users.followers` | `follows`, `users` |
| 16 | GET | `/users/{username}/following` | 선택 | `users.following` | `follows`, `users` |
| 17 | GET | `/search` | 선택 | `users.searchAll` | `users`, `hashtags`, `post_hashtags`, `posts` |
| 18 | POST | `/posts` | 필수 | `posts.createPost` | `posts`, `post_images`, `hashtags`, `post_hashtags` |
| 19 | GET | `/posts/feed` | 선택 | `posts.feed` | `posts`, `follows`, `likes`, `saved_posts` |
| 20 | GET | `/posts/explore` | 선택 | `posts.explore` | `posts`, `post_images`, `follows` |
| 21 | GET | `/posts/{id}` | 선택 | `posts.getPost` | `posts`, `post_images`, `likes`, `comments`, `saved_posts` |
| 22 | DELETE | `/posts/{id}` | 필수 | `posts.deletePost` | `posts` (+ CASCADE) |
| 23 | POST | `/posts/{id}/like` | 필수 | `posts.likePost` | `likes`, `notifications` |
| 24 | DELETE | `/posts/{id}/like` | 필수 | `posts.unlikePost` | `likes` |
| 25 | POST | `/posts/{id}/save` | 필수 | `posts.savePost` | `saved_posts` |
| 26 | DELETE | `/posts/{id}/save` | 필수 | `posts.unsavePost` | `saved_posts` |
| 27 | GET | `/posts/{id}/comments` | 선택 | `posts.listComments` | `comments`, `users` |
| 28 | POST | `/posts/{id}/comments` | 필수 | `posts.addComment` | `comments`, `notifications` |
| 29 | DELETE | `/comments/{id}` | 필수 | `posts.deleteComment` | `comments` |
| 30 | POST | `/stories` | 필수 | `stories.createStory` | `stories` |
| 31 | GET | `/stories/feed` | 필수 | `stories.storyFeed` | `stories`, `story_views`, `follows` |
| 32 | POST | `/stories/{id}/view` | 필수 | `stories.viewStory` | `story_views` |
| 33 | DELETE | `/stories/{id}` | 필수 | `stories.deleteStory` | `stories` |
| 34 | GET | `/conversations` | 필수 | `messages.conversations` | `conversations`, `conversation_members`, `messages` |
| 35 | POST | `/conversations` | 필수 | `messages.createConversation` | `conversations`, `conversation_members` |
| 36 | GET | `/conversations/{id}/messages` | 필수 | `messages.listMessages` | `messages` |
| 37 | POST | `/conversations/{id}/messages` | 필수 | `messages.sendMessage` | `messages`, `conversations.updated_at` |
| 38 | POST | `/conversations/{id}/read` | 필수 | `messages.readConversation` | `conversation_members.last_read_message_id` |
| 39 | GET | `/notifications` | 필수 | `notifications.listNotifications` | `notifications`, `users` (actor) |
| 40 | POST | `/notifications/read` | 필수 | `notifications.readNotifications` | `notifications.read` |
| 41 | DELETE | `/notifications/{id}` | 필수 | `notifications.deleteNotification` | `notifications` |

**제거·미노출 (프론트 미사용):**

- `GET /users/me` — 세션은 `GET /auth/me`만 사용
- `GET /stories/{id}` — 스토리 데이터는 `GET /stories/feed` 묶음만 사용
- 알림 일괄 DELETE, 게시 PATCH, 댓글 좋아요, WebSocket 등 §1.1 항목

**쓰기 시 DB 부가 규칙:**

- `POST /posts` 캡션 `#태그` → `hashtags` / `post_hashtags`. `@username`은 댓글·알림에서만 `mention`
- `POST /users/{username}/follow` → `notifications` `type=follow` (CHECK 형태 준수)
- `POST /posts/{id}/like` → `notifications` `type=like`, `post_id` 필수
- `POST /posts/{id}/comments` → `comment` + 본문 `@` → `mention`. `comment_preview` 스냅샷
- `POST /conversations` → `user_low_id`/`user_high_id` 정렬 후 기존 행 재사용
- `GET /users/{username}/saved` 정렬·커서는 **`saved_posts.created_at`**, 게시물 `created_at` 아님

### 6.1 인증

`POST /auth/signup`  
`{ email, username, full_name, password }` → `201` `{ access_token, token_type, user }`  
중복 `409` 이미 사용 중인 이메일 또는 사용자 이름.

`POST /auth/login`  
`{ username, password }` → `200` 동일 토큰 응답. 실패 `401` 사용자 이름 또는 비밀번호가 올바르지 않습니다.

`GET /auth/me`  
프로필 + `posts_count`, `followers_count`, `following_count`. 본인이면 `show_activity_status` 포함.

`POST /auth/password` (로그인)  
`{ current_password, new_password }` → `{ ok: true }`  
현재 비밀번호 틀림 `400`. 새 비밀번호가 같으면 `400`.

### 6.2 사용자

`GET /users/suggested?limit=5`  
게스트 가능. 로그인 시 본인·팔로잉 제외. 응답: **`UserPublic[]`** (배열).

`PATCH /users/me` `{ full_name?, bio?, website? }` → 프로필 객체 (`GET /auth/me`와 동일 필드)

`POST /users/me/avatar` multipart `file`

`GET /users/me/privacy` `{ is_private, show_activity_status }`

`PATCH /users/me/privacy` `{ is_private?, show_activity_status? }` → 동일 형태

`GET /users/{username}`  
`UserPublic` + 카운트. `is_private`, `is_following`, `is_me`.

`GET /users/{username}/posts` 그리드: `{ id, cover_url, likes_count, comments_count, image_count }`

`GET /users/{username}/saved` 본인만. 타인 `403`. 커서는 `saved_posts.created_at` + `post_id`.

`POST` / `DELETE /users/{username}/follow`  
본인 팔로우 `400`. 팔로우 시 알림 `follow` (자기 자신 제외).

`GET /users/{username}/followers`  
`GET /users/{username}/following`  
`{ items: UserPublic[] }`

### 6.3 게시물

`POST /posts` multipart: `files`(1~10), `caption`(≤2200), `location`(≤100)  
캡션 `#태그` → hashtags. 응답 `PostPublic`.

`GET /posts/feed`  
`GET /posts/explore` 그리드 아이템  
`GET /posts/{id}` `PostPublic`  
`DELETE /posts/{id}` 작성자만

`POST` / `DELETE /posts/{id}/like` 멱등. 좋아요 시 알림 `like`  
`POST` / `DELETE /posts/{id}/save` 멱등

`PostPublic`:

```json
{
  "id": 1,
  "author": { "id": 1, "username": "demo", "full_name": "데모 사용자", "avatar_url": "/media/avatars/demo.png", "bio": "...", "website": null, "is_following": false, "is_me": false, "is_private": false },
  "caption": "클론의 첫 게시물 #한국",
  "location": "",
  "images": [{ "id": 1, "url": "/media/posts/p4.png", "position": 0 }],
  "likes_count": 0,
  "comments_count": 1,
  "liked": false,
  "saved": false,
  "created_at": "2026-11-02T01:00:00Z"
}
```

게스트의 `liked`/`saved`/`is_following`/`is_me`는 false.

### 6.4 댓글

`GET /posts/{post_id}/comments` → `{ items: [{ id, author, body, created_at }], next_cursor }`  
`POST /posts/{post_id}/comments` `{ body }` `201`. 알림 `comment`. 본문 `@username`이면 `mention`  
`DELETE /comments/{comment_id}` 댓글 작성자 또는 게시 작성자

### 6.5 스토리

`POST /stories` multipart `file` 1장 (로그인 피드에서만)  
`GET /stories/feed` 팔로잉+본인, 유저별 그룹. 본인 그룹 맨 앞. `created_at` 24시간 이내만.

```json
{
  "items": [
    {
      "user": { },
      "has_unseen": true,
      "stories": [{ "id": 1, "media_url": "/media/stories/alice.png", "created_at": "...", "seen": false }]
    }
  ]
}
```

`POST /stories/{id}/view` → `story_views` `(story_id, user_id)` 유니크. 본인 스토리 조회는 행을 넣지 않아도 된다.  
`DELETE /stories/{id}` 작성자만. `stories` CASCADE로 `story_views` 삭제.

(`GET /stories/{id}`는 §6.0 제외 목록 — 구현하지 않음.)

### 6.6 검색

`GET /search?q=`  
프론트는 `q`만 보낸다. 응답 `{ users, hashtags: [{ name, posts_count }], posts }` (그리드).

### 6.7 DM

`GET /conversations`  
아이템: `{ id, other_user, last_message: { id, body, sender_id, created_at } | null, unread_count }`

`POST /conversations` `{ username }` 기존 스레드 재사용. 같은 두 유저는 `conversations.user_low_id` / `user_high_id` 한 행만 있다.

`GET /conversations/{id}/messages` `{ items, next_cursor }` 오래된→최신으로 돌려준다.

`POST /conversations/{id}/messages` `{ body }` 1~2000자

`POST /conversations/{id}/read` 상대가 보낸 메시지를 읽음 (`last_read_message_id`)

참가자 아니면 `403`. 이미지 메시지 없음.

### 6.8 알림

`GET /notifications`  
`{ items, next_cursor, has_unread }`  
아이템: `{ id, type, actor, post_id, comment_preview, read, created_at }`

`POST /notifications/read` 해당 유저의 `read=0` 행을 모두 `1`로. 프론트는 목록 로드 후 본문 없이 호출. **행을 지우지 않는다.** (선택적 `{ ids }` 필터는 프론트 미사용 — 서버는 전체 읽음만 처리해도 된다.)

`DELETE /notifications/{id}` **해당 유저의 그 행만** 삭제. 전체 삭제 엔드포인트 금지.

알림 문구는 프론트가 `type`으로 조립한다. `like`/`comment`/`mention`은 `post_id` 없이 넣지 않는다. `follow`는 `post_id`를 넣지 않는다.

---

## 7. 시드 (검수)

유저가 없으면 생성. 메시지가 없으면 DM 시드. 탐색/알림 더미는 idempotent.

| username | password | 역할 |
|----------|----------|------|
| demo | demo1234 | 메인 검수 |
| alice, bob | demo1234 | 피드·DM |
| cara, dan | demo1234 | 탐색(demo가 안 팔로우) |

- 게시 캡션·위치·댓글은 한국어. 플레이스홀더 이미지는 최소 PNG 재사용
- DM: demo↔alice(미읽음 1), demo↔bob
- 알림(demo): follow는 항상. like/comment/mention은 **demo 게시물이 있을 때만** 그 `post_id`로 넣는다. 게시물이 없으면 그 세 종류는 만들지 않는다. 행 단위이며 전체 삭제 없음

기동: `seed_if_empty` → `seed_messages_if_empty` → `seed_explore_and_activity`

---

## 8. 프로젝트 구조 (현재)

```
backend/
  app/
    main.py
    config.py
    database.py          # engine, run_migrations, get_db
    migrate.py           # CLI: create_all + run_migrations
    deps.py              # get_current_user, get_optional_user
    models.py
    schemas.py
    seed.py
    services.py
    routers/
      auth.py users.py posts.py comments.py
      stories.py search.py conversations.py notifications.py
    utils/security.py media.py time.py
  uploads/
  requirements.txt
  instagram.db           # gitignore
```

---

## 9. 완료 기준

프론트 `npm run dev`와 이 API가 맞으면 된다.

- [ ] 게스트가 `/` 피드·탐색·상세·프로필을 보고, 좋아요/댓글/만들기는 `/login`으로 보낸다
- [ ] `demo` 로그인 후 피드(팔로잉), 스토리, DM 2스레드, 알림, 설정이 동작한다
- [ ] 알림 **삭제 1건**만 사라지고 나머지는 남는다 (`DELETE /notifications/{id}` 200)
- [ ] 비밀번호 변경·비공개 계정이 SQLite에 반영된다
- [ ] 개발·프로덕트 모두 `DATABASE_URL`이 `sqlite://` 이다
- [ ] `/docs`에 §6.0 표의 **41개** 엔드포인트만 있다 (`GET /users/me`, `GET /stories/{id}` 없음)
