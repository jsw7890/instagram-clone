from collections import defaultdict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Story, StoryView, User
from app.services import following_ids, user_public
from app.utils.media import delete_media, save_upload
from app.utils.time import now_iso, story_cutoff_iso

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post("", status_code=201)
def create_story(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    url = save_upload(file, "stories")
    story = Story(user_id=current.id, media_url=url, created_at=now_iso())
    db.add(story)
    db.commit()
    db.refresh(story)
    return {"id": story.id, "media_url": story.media_url, "created_at": story.created_at, "seen": False}


@router.get("/feed")
def feed(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    cutoff = story_cutoff_iso()
    ids = following_ids(db, current.id) + [current.id]
    stories = db.scalars(
        select(Story)
        .where(Story.user_id.in_(ids), Story.created_at >= cutoff)
        .order_by(Story.created_at.asc())
    ).all()
    grouped: dict[int, list[Story]] = defaultdict(list)
    for s in stories:
        grouped[s.user_id].append(s)
    seen_pairs = set(
        db.execute(
            select(StoryView.story_id, StoryView.user_id).where(StoryView.user_id == current.id)
        ).all()
    )
    items = []
    for uid, group in grouped.items():
        author = db.get(User, uid)
        if not author:
            continue
        payload_stories = []
        unseen = False
        for s in group:
            seen = (s.id, current.id) in seen_pairs
            if not seen:
                unseen = True
            payload_stories.append(
                {"id": s.id, "media_url": s.media_url, "created_at": s.created_at, "seen": seen}
            )
        items.append(
            {
                "user": user_public(db, author, current),
                "has_unseen": unseen,
                "stories": payload_stories,
            }
        )
    items.sort(key=lambda x: (0 if x["user"].id == current.id else 1, 0 if x["has_unseen"] else 1))
    return {"items": items}


@router.post("/{story_id}/view")
def view_story(story_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="스토리를 찾을 수 없습니다")
    if story.user_id != current.id:
        existing = db.get(StoryView, (story.id, current.id))
        if not existing:
            db.add(StoryView(story_id=story.id, user_id=current.id, created_at=now_iso()))
            db.commit()
    return {"ok": True}


@router.delete("/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="스토리를 찾을 수 없습니다")
    if story.user_id != current.id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    delete_media(story.media_url)
    db.delete(story)
    db.commit()
    return {"ok": True}
