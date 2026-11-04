# 프론트엔드 명세서 (React)

Instagram 클론 웹 애플리케이션의 클라이언트 요구사항이다. 백엔드 계약은 `backend.md`, 데이터 모델은 `db.md`, 실행·폴더 구조는 `guide.md`를 따른다.

## 1. 목표

Instagram 웹과 유사한 **피드 중심 SNS**를 브라우저에서 제공한다.

- 회원가입 / 로그인 / 로그아웃
- 이미지 게시물(캐러셀), 캡션, 해시태그
- 좋아요, 댓글, 저장
- 팔로우 / 언팔로우
- 프로필, 탐색, 검색
- 스토리(24시간)
- DM, 알림

## 2. 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 런타임 | React 18 + Vite | SPA |
| 언어 | JavaScript (JSX) | TypeScript 미사용 |
| 라우팅 | React Router v6 | |
| HTTP | Axios | `Authorization: Bearer` |
| 스타일 | CSS Modules + 전역 `variables.css` | Instagram 라이트 테마 |
| 상태 | React Context + 로컬 상태 | 전역 스토어 라이브러리 없음 |
| 폼 | 제어 컴포넌트 | |
| 이미지 | `<input type="file">` + `FormData` | 미리보기 URL 사용 |

Node.js 18+, 개발 서버 포트 **5173**. API 베이스는 `VITE_API_BASE_URL` (기본 `http://localhost:8000/api`).

## 3. 디자인 시스템

Instagram 웹(데스크톱)을 기준으로 한다. 픽셀 퍼펙트 복제는 요구하지 않되, 레이아웃·간격·타이포는 비슷해야 한다.

### 3.1 색상

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--bg` | `#ffffff` | 페이지 배경 |
| `--bg-secondary` | `#fafafa` | 사이드·입력 배경 |
| `--text` | `#262626` | 본문 |
| `--text-secondary` | `#8e8e8e` | 보조 문구 |
| `--border` | `#dbdbdb` | 구분선 |
| `--primary` | `#0095f6` | 버튼, 링크 |
| `--danger` | `#ed4956` | 좋아요 활성, 삭제 |
| `--story-ring` | `linear-gradient(45deg, #f58529, #dd2a7b, #8134af)` | 미시청 스토리 |

### 3.2 레이아웃

- 최대 콘텐츠 폭: 피드 `630px`, 우측 추천 `319px` (뷰포트 ≥ 1160px일 때)
- 좌측 고정 사이드바: 너비 `244px` (좁은 화면 `72px` 아이콘만)
- 모바일(≤ 767px): 하단 탭 바, 사이드바 숨김
- 본문 폰트: system-ui, 본문 14px, 사용자명 14px semibold

### 3.3 공통 UI 규칙

- 원형 아바타: 스토리 링 있을 때 외곽 그라데이션 + 흰 갭 2px
- 버튼: Primary(파란 채움), Ghost(텍스트), Danger(빨간 텍스트)
- 모달: 반투명 오버레이, 중앙 카드, `Esc`/오버레이 클릭 닫기
- 로딩: 스켈레톤 또는 중앙 스피너. 빈 목록은 안내 문구 + CTA
- 에러: 토스트(상단, 3초) 또는 인라인 메시지. 401이면 로그인으로 이동

## 4. 라우팅

인증이 필요한 라우트는 `ProtectedRoute`로 감싼다. 토큰이 없으면 `/login`으로 리다이렉트하고 `from` 쿼리로 복귀 경로를 남긴다.

| 경로 | 페이지 | 인증 |
|------|--------|------|
| `/login` | 로그인 | 비로그인 전용 |
| `/signup` | 회원가입 | 비로그인 전용 |
| `/` | 홈 피드 | 선택(게스트 읽기 가능) |
| `/explore` | 탐색 그리드 | 선택 |
| `/search` | 검색 결과 | 선택 |
| `/p/:postId` | 게시물 상세 | 선택 |
| `/:username` | 프로필 | 선택 |
| `/direct` | DM 목록 | 필요 |
| `/direct/:conversationId` | DM 스레드 | 필요 |
| `/activity` | 알림 | 필요 |
| `/settings` | 설정 메뉴 | 필요 |
| `/settings/password` | 비밀번호 변경 | 필요 |
| `/settings/privacy` | 개인정보(비공개 계정 등) | 필요 |
| `/:username/saved` | 저장한 게시물 | 본인만 |
| `/admin/login` | 관리자 로그인 | 비로그인 전용 |
| `/admin` | 관리자 대시보드 | 관리자만 |
| `/admin/users` | 관리자 - 사용자 관리 | 관리자만 |
| `/admin/posts` | 관리자 - 게시물 관리 | 관리자만 |
| `/not-found`, `*` | 404 (`*`는 `/not-found`로 리다이렉트) | - |

게시 작성과 팔로워/팔로잉 목록은 **별도 라우트가 아니라 모달**이다(아래 §6.6, §6.8 참고).

로그인된 사용자가 `/login`, `/signup`에 오면 `/`로 보낸다. 로그인 성공 시 `is_admin`이면 `/admin`으로, 아니면 원래 가려던 경로(`from`) 또는 `/`로 보낸다. `/admin/*`은 `AdminRoute`(비관리자 403/리다이렉트)로 보호되고, `AdminLayout`이 공통 레이아웃을 제공한다.

## 5. 전역 상태 (Context)

### 5.1 `AuthContext`

| 값 | 설명 |
|----|------|
| `user` | `{ id, username, full_name, avatar_url, bio }` 또는 `null` (관리자면 `is_admin: 1`) |
| `token` | JWT 문자열 또는 `null` |
| `login(username, password)` | 사용자명 또는 이메일 모두 허용. 성공 시 토큰·유저 저장 |
| `signup(payload)` | 가입 후 자동 로그인 |
| `logout()` | 토큰 삭제, `/login` |
| `refreshMe()` | `GET /users/me`로 프로필 동기화 |
| `loading` | 초기 토큰 검증 중 |

토큰은 `localStorage` 키 `ig_token`에 저장한다. Axios 인터셉터가 요청 헤더에 붙인다. 401 응답 시 로그아웃.

### 5.2 `ToastContext`

`success(message)`, `error(message)`만 제공한다.

### 5.3 그 외

피드, 알림, DM은 페이지 로컬 상태 + React Query 없이 `useEffect` 페칭. 스토리 뷰어는 모달 로컬 상태.

## 6. 페이지 명세

### 6.1 로그인 `/login`

Instagram 로고, 이메일(또는 username), 비밀번호, 로그인 버튼, 회원가입 링크, 관리자 로그인 링크(`/admin/login`), 로그인 없이 둘러보기 링크(`/`).

- 검증: 둘 다 비어 있으면 버튼 비활성. 실패 시 `detail` 메시지 표시
- 성공: `is_admin`이면 `/admin`, 아니면 `from` 또는 `/`로 이동

### 6.2 회원가입 `/signup`

이메일, 성명, 사용자명, 비밀번호(8자 이상), 로그인 없이 둘러보기 링크.

- 사용자명은 영문·숫자·`.` `_`만, 실시간 중복은 제출 시 서버 에러로 처리
- 성공 후 자동 로그인 → `/`

### 6.3 홈 피드 `/`

좌측 내비 + 중앙 피드 + (와이드) 우측 “회원님을 위한 추천”.

**스토리 바**

- 가로 스크롤. 본인 스토리가 맨 앞(“내 스토리”, 없으면 `+`)
- 클릭 시 전체화면 스토리 뷰어
- 미시청: 그라데이션 링, 시청 완료: 회색 링

**피드 카드** (`PostCard`)

1. 헤더: 아바타(스토리 링 가능), username, 더보기(본인 글 삭제)
2. 미디어: 정사각 또는 원본 비율, 여러 장이면 좌우 화살표 + 점 인디케이터
3. 액션: 좋아요, 댓글(상세 포커스), 공유(링크 복사), 저장
4. 좋아요 수, 캡션(username + 더보기 접기 125자), 댓글 미리보기 최대 2개
5. 댓글 입력(엔터 제출)

**무한 스크롤**: `GET /posts/feed?cursor=&limit=10`. 마지막 카드 근처 Intersection Observer. `next_cursor`가 `null`이면 종료.

**우측 패널**: 현재 유저, `GET /users/suggested?limit=5`, 팔로우 버튼.

### 6.4 탐색 `/explore`

`GET /posts/explore` 결과. 3열 정사각 그리드. 호버 시 좋아요·댓글 수. 클릭 → `/p/:postId`.

### 6.5 검색 `/search?q=`

상단 또는 사이드 검색 입력. `q`가 2자 이상일 때 `GET /search?q=&type=users,hashtags,posts`.

탭: 계정 / 태그 / 게시물. 계정은 리스트, 태그는 `#tag · N게시물`, 게시물은 그리드.

### 6.6 게시 작성

데스크톱·모바일 공통: 사이드바/하단 탭 "만들기" → `CreatePost` 모달(별도 라우트 없음).

단계:

1. 파일 선택(이미지 `image/jpeg`, `image/png`, `image/webp`, 최대 10장, 장당 10MB)
2. 미리보기 캐러셀, 캡션(2,200자), 위치 텍스트(선택, 100자)
3. 공유 → `POST /posts` multipart. 성공 시 모달 닫고 피드 갱신 또는 `/p/:id`

### 6.7 게시물 상세 `/p/:postId`

Instagram 상세처럼 **왼쪽 미디어, 오른쪽 메타**(데스크톱). 좁은 화면은 세로 스택.

- 댓글 목록 스크롤, 하단 고정 입력
- 좋아요, 저장, 작성 시각 상대 표기(`방금`, `3분`, `2시간`, `1일`)
- 본인 게시물: 삭제 확인 후 `DELETE /posts/:id` → `/`
- 본인 댓글: 삭제

### 6.8 프로필 `/:username`

헤더: 큰 아바타, 사용자명, 팔로우/언팔로우 또는 "프로필 편집", 통계(게시물·팔로워·팔로잉), 성명, 바이오. 팔로워/팔로잉 수 클릭 시 **별도 라우트가 아니라 `Modal`**(`openList("followers"|"following")`)로 목록을 띄운다.

탭: 게시물 그리드 / 저장(본인만, `/:username/saved`). 게시물 없음 문구: "게시물 없음".

**프로필 편집 모달**: 아바타 업로드, 성명, 바이오(150자), 웹사이트. `PATCH /users/me` + 선택 시 `POST /users/me/avatar`.

### 6.9 스토리 뷰어

전체화면, 어두운 배경. 상단 진행 바(사용자당 스토리 수만큼). 기본 5초 자동 진행, 클릭 좌/우로 이전/다음. 본인 스토리는 조회 수, 삭제.

업로드: 홈 스토리 바 `+` → 이미지 1장 `POST /stories`.

### 6.10 DM

`/direct`: 대화 목록(상대 아바타, 마지막 메시지, 시각, 읽지 않음 점).

`/direct/:id`: 메시지 버블(본인 우측), 하단 입력. 3초 폴링으로 새 메시지 반영.

새 메시지: 사용자 검색 후 `POST /conversations`.

### 6.11 알림 `/activity`

`GET /notifications`. 종류별 문구:

| type | 문구 예 |
|------|---------|
| `follow` | `{user}님이 회원님을 팔로우하기 시작했습니다.` |
| `like` | `{user}님이 회원님의 게시물을 좋아합니다.` |
| `comment` | `{user}님이 댓글을 남겼습니다: {preview}` |
| `mention` | `{user}님이 회원님을 언급했습니다.` |

읽지 않은 항목 강조. 페이지 진입 시 `POST /notifications/read`. 사이드바 하트 아이콘에 미읽음 뱃지.

### 6.12 설정 `/settings`, `/settings/password`, `/settings/privacy`

`SettingsPages.jsx` 한 파일에서 `SettingsHome`, `PasswordSettings`, `PrivacySettings` 세 컴포넌트를 export한다.

- `/settings`: 메뉴(비밀번호 변경, 개인정보로 이동)
- `/settings/password`: 현재 비밀번호·새 비밀번호 → `POST /auth/password`
- `/settings/privacy`: 비공개 계정·활동 상태 토글 → `GET`/`PATCH /users/me/privacy`

### 6.13 관리자 `/admin/*`

일반 사용자 화면과 완전히 분리된 레이아웃(`AdminLayout`)과 보호 라우트(`AdminRoute`, 비관리자는 접근 불가)를 쓴다.

- `/admin/login`: 관리자 전용 로그인 폼 → 성공 시 `/admin`
- `/admin` (`AdminDashboard`): `GET /admin/stats` — 전체 유저·게시물·댓글·좋아요·팔로우·메시지·스토리 수, 최근 7일 가입자 수·게시물 수, 최근 가입자 목록
- `/admin/users` (`AdminUsersPage`): `GET /admin/users` 검색·페이지네이션 목록, `DELETE /admin/users/{id}` 탈퇴 처리(관리자·본인 계정은 삭제 불가)
- `/admin/posts` (`AdminPostsPage`): `GET /admin/posts` 검색·페이지네이션 목록, `DELETE /admin/posts/{id}` 삭제

## 7. 컴포넌트 목록

```
src/
  api/client.js          # axios 인스턴스, 인터셉터
  api/auth.js
  api/posts.js
  api/users.js
  api/stories.js
  api/messages.js        # conversations, openConversation, messages, sendMessage, readConversation
  api/notifications.js
  api/admin.js           # stats, users, deleteUser, posts, deletePost
  context/AuthContext.jsx
  context/ToastContext.jsx
  components/
    Icons.jsx
    layout/Sidebar.jsx
    layout/BottomNav.jsx
    layout/AppShell.jsx
    layout/MobileHeader.jsx
    layout/SiteFooter.jsx
    post/PostCard.jsx
    post/PostGrid.jsx
    post/CreatePost.jsx   # 게시 작성 모달
    story/StoryBar.jsx
    story/StoryViewer.jsx
    user/Avatar.jsx
    user/FollowButton.jsx
    user/ProfileMessageButton.jsx
    user/SuggestedUsers.jsx
    admin/AdminLayout.jsx
    common/Modal.jsx
    common/ProtectedRoute.jsx
    common/AdminRoute.jsx
  pages/
    LoginPage.jsx
    SignupPage.jsx
    FeedPage.jsx
    ExplorePage.jsx
    SearchPage.jsx
    PostDetailPage.jsx
    ProfilePage.jsx
    DirectPages.jsx        # DirectListPage, DirectThreadPage (named export)
    ActivityPage.jsx
    SettingsPages.jsx      # SettingsHome, PasswordSettings, PrivacySettings
    NotFoundPage.jsx
    admin/AdminLoginPage.jsx
    admin/AdminDashboard.jsx
    admin/AdminUsersPage.jsx
    admin/AdminPostsPage.jsx
  utils/format.js        # 상대시간, 숫자 축약(1.2만)
  utils/media.js
  App.jsx
  main.jsx
```

## 8. API 연동 규칙

- JSON: `Content-Type: application/json`
- 업로드: `multipart/form-data`. 필드명은 `backend.md`와 동일
- 페이지네이션: `cursor`(opaque string), `limit`. 응답 `{ items, next_cursor }`
- 좋아요/저장/팔로우는 **낙관적 업데이트** 후 실패 시 롤백 + 토스트
- 이미지 URL은 백엔드가 준 절대/상대 경로를 `VITE_API_ORIGIN`과 조합해 표시

날짜는 ISO 8601. 표시만 프론트에서 상대시간으로 변환한다.

## 9. 접근성·품질

- 아이콘 버튼은 `aria-label` (좋아요, 댓글, 저장 등)
- 모달 `role="dialog"`, 포커스 트랩은 필수 아님
- 키보드: 댓글 입력 Enter 제출, Shift+Enter 줄바꿈
- 반응형: 375 / 768 / 1280 폭에서 깨지지 않을 것

## 10. 완료 기준 (프론트)

- [ ] 비로그인 사용자는 보호 라우트에 접근할 수 없다
- [ ] 피드·탐색·프로필·상세·작성·좋아요·댓글·팔로우가 동작한다
- [ ] 스토리 업로드·열람·만료(24h, 서버 기준)가 동작한다
- [ ] DM 송수신이 폴링으로 보인다
- [ ] 알림 목록과 미읽음 뱃지가 동작한다
- [ ] 로그인/피드/프로필/상세가 데스크톱·모바일 레이아웃으로 보인다
