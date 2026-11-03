from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_optional_user
from app.models import Hashtag, Post, PostHashtag, User
from app.services import grid_post, user_public

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    type: str = "users,hashtags,posts",
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    qn = q.strip().lstrip("#")
    kinds = {k.strip() for k in type.split(",") if k.strip()}
    result = {"users": [], "hashtags": [], "posts": []}
    if "users" in kinds:
        users = db.scalars(
            select(User)
            .where(User.is_admin == 0, or_(User.username.like(f"%{qn.lower()}%"), User.full_name.like(f"%{qn}%")))
            .limit(limit)
        ).all()
        result["users"] = [user_public(db, u, current) for u in users]
    if "hashtags" in kinds:
        tags = db.execute(
            select(Hashtag.name, func.count(PostHashtag.post_id))
            .outerjoin(PostHashtag, PostHashtag.hashtag_id == Hashtag.id)
            .where(Hashtag.name.like(f"{qn.lower()}%"))
            .group_by(Hashtag.id)
            .limit(limit)
        ).all()
        result["hashtags"] = [{"name": n, "posts_count": c} for n, c in tags]
    if "posts" in kinds:
        tag = db.scalar(select(Hashtag).where(Hashtag.name == qn.lower()))
        post_q = select(Post)
        if tag:
            post_q = post_q.join(PostHashtag, PostHashtag.post_id == Post.id).where(
                PostHashtag.hashtag_id == tag.id
            )
        else:
            post_q = post_q.where(Post.caption.like(f"%{qn}%"))
        posts = db.scalars(post_q.order_by(Post.created_at.desc()).limit(limit)).all()
        result["posts"] = [grid_post(db, p) for p in posts]
    return result
