from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine, run_migrations
from app.models import *  # noqa: F401,F403
from app.routers import admin, auth, comments, conversations, notifications, posts, search, stories, users
from app.seed import ensure_admin_user, ensure_demo_alice_unread, seed_explore_and_activity, seed_if_empty, seed_messages_if_empty
from app.utils.media import upload_root

Base.metadata.create_all(bind=engine)
run_migrations()
upload_root()

with SessionLocal() as db:
    seed_if_empty(db)
    seed_messages_if_empty(db)
    seed_explore_and_activity(db)
    ensure_demo_alice_unread(db)
    ensure_admin_user(db)

app = FastAPI(title="Instagram Clone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(stories.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

media_dir = Path(settings.upload_dir)
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
