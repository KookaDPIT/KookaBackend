"""Utilizatori: /me, profil public, urmărire (follow) și pașaport culinar."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user, get_current_user_optional

router = APIRouter(tags=["users"])


@router.get("/me")
def me(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return serializers.user_to_dict(db, user, viewer=user)


@router.patch("/me")
def update_me(
    data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    payload = data.model_dump(exclude_none=True)
    for field, value in payload.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return serializers.user_to_dict(db, user, viewer=user)


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    return serializers.user_to_dict(db, u, viewer=viewer)


@router.get("/users/{user_id}/recipes")
def user_recipes(user_id: int, db: Session = Depends(get_db)):
    recipes = (
        db.query(models.Recipe)
        .filter(
            models.Recipe.author_id == user_id,
            models.Recipe.moderation_status == "ok",
        )
        .order_by(models.Recipe.created_at.desc())
        .all()
    )
    return [serializers.recipe_to_dict(db, r) for r in recipes]


@router.post("/users/{user_id}/follow", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if user_id == user.id:
        raise HTTPException(400, "Nu te poți urmări pe tine")
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "Utilizatorul nu există")

    existing = (
        db.query(models.Follow)
        .filter(
            models.Follow.follower_id == user.id,
            models.Follow.following_id == user_id,
        )
        .first()
    )
    if not existing:
        db.add(models.Follow(follower_id=user.id, following_id=user_id))
        db.commit()
    return {"following": True}


@router.delete("/users/{user_id}/follow")
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Follow).filter(
        models.Follow.follower_id == user.id,
        models.Follow.following_id == user_id,
    ).delete()
    db.commit()
    return {"following": False}


@router.get("/users/{user_id}/followers")
def followers(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.User)
        .join(models.Follow, models.Follow.follower_id == models.User.id)
        .filter(models.Follow.following_id == user_id)
        .all()
    )
    return [serializers.user_to_dict(db, u, viewer) for u in rows]


@router.get("/users/{user_id}/following")
def following(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.User)
        .join(models.Follow, models.Follow.following_id == models.User.id)
        .filter(models.Follow.follower_id == user_id)
        .all()
    )
    return [serializers.user_to_dict(db, u, viewer) for u in rows]


@router.get("/users/{user_id}/passport")
def passport(user_id: int, db: Session = Depends(get_db)):
    """Țări distincte din rețetele autorate + rețetele gătite-verificate."""
    counts = {}

    authored = (
        db.query(models.Recipe.origin)
        .filter(models.Recipe.author_id == user_id, models.Recipe.origin != "")
        .all()
    )
    for (origin,) in authored:
        key = origin.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1

    cooked = (
        db.query(models.Recipe.origin)
        .join(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.cooked_verified == True,
            models.Recipe.origin != "",
        )
        .all()
    )
    for (origin,) in cooked:
        key = origin.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1

    countries = [{"country": k, "count": v} for k, v in sorted(counts.items())]
    return {"countries": countries, "total": len(countries)}
