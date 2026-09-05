"""Căutare globală: rețete (nume/țară) + utilizatori (username/nume)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import serializers
from database import get_db
from deps import get_current_user_optional
from services import visibility

router = APIRouter(tags=["search"])


@router.get("/search")
def search(
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    q = q.strip()
    if not q:
        return {"recipes": [], "users": []}
    like = f"%{q.lower()}%"

    hidden = visibility.hidden_author_ids(db, viewer)

    recipes = visibility.visible_authors(
        db.query(models.Recipe), models.Recipe, hidden
    )
    recipes = (
        recipes
        .filter(
            models.Recipe.moderation_status == "ok",
            or_(
                func.lower(models.Recipe.title).like(like),
                func.lower(models.Recipe.origin).like(like),
            ),
        )
        .order_by(models.Recipe.created_at.desc())
        .limit(20)
        .all()
    )

    # un cont suspendat/blocat nu trebuie să apară nici în căutare
    users_q = db.query(models.User).filter(
        models.User.is_active == True,
        or_(
            func.lower(models.User.username).like(like),
            func.lower(models.User.full_name).like(like),
        ),
    )
    if hidden:
        users_q = users_q.filter(models.User.id.notin_(hidden))
    users = users_q.limit(20).all()

    return {
        "recipes": [serializers.recipe_to_dict(db, r, viewer=viewer) for r in recipes],
        "users": [serializers.user_to_dict(db, u, viewer) for u in users],
    }
