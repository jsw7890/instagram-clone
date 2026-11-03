import re

from pydantic import BaseModel, Field, field_validator

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str
    avatar_url: str | None = None
    bio: str | None = None
    website: str | None = None
    is_following: bool = False
    is_me: bool = False
    is_private: bool = False

    model_config = {"from_attributes": True}


class UserProfile(UserPublic):
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0


USERNAME_RE = re.compile(r"^[a-zA-Z0-9._]{1,30}$")


class SignupIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    username: str = Field(min_length=1, max_length=30)
    full_name: str = Field(default="", max_length=50)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError(
                "사용자 이름은 영문, 숫자, 밑줄(_), 마침표(.)만 1~30자까지 사용할 수 있습니다"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        return v


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=150)
    website: str | None = Field(default=None, max_length=200)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class PrivacyUpdate(BaseModel):
    is_private: bool | None = None
    show_activity_status: bool | None = None


class PrivacyOut(BaseModel):
    is_private: bool
    show_activity_status: bool


class ImageOut(BaseModel):
    id: int
    url: str
    position: int


class PostPublic(BaseModel):
    id: int
    author: UserPublic
    caption: str
    location: str
    images: list[ImageOut]
    likes_count: int
    comments_count: int
    liked: bool
    saved: bool
    created_at: str


class GridPost(BaseModel):
    id: int
    cover_url: str | None
    likes_count: int
    comments_count: int
    image_count: int


class Page(BaseModel):
    items: list
    next_cursor: str | None = None


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2200)


class CommentOut(BaseModel):
    id: int
    author: UserPublic
    body: str
    created_at: str


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ConversationCreate(BaseModel):
    username: str
