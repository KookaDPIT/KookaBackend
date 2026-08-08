"""Conversie obiecte ORM -> dict pentru răspunsuri JSON.

Aici se face deserializarea câmpurilor text-JSON (ingredients, steps,
nutrition, allergens, images) și calculul câmpurilor derivate (rating mediu,
număr recenzii, urmăritori)."""
import json
from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def _load_json(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def recipe_stats(db: Session, recipe_id: int):
    """(avg_rating, review_count, saves) pentru o rețetă."""
    avg, count = (
        db.query(func.avg(models.Review.rating), func.count(models.Review.id))
        .filter(models.Review.recipe_id == recipe_id)
        .first()
    )
    saves = (
        db.query(func.count(models.SavedRecipe.id))
        .filter(models.SavedRecipe.recipe_id == recipe_id)
        .scalar()
    )
    return (round(float(avg), 1) if avg else 0.0), int(count or 0), int(saves or 0)


def author_mini(user: "models.User"):
    if user is None:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url or "",
    }


def recipe_to_dict(db: Session, r: "models.Recipe", full: bool = False):
    """Card (full=False) sau detaliu complet (full=True)."""
    avg, count, saves = recipe_stats(db, r.id)
    data = {
        "id": r.id,
        "title": r.title,
        "description": r.description or "",
        "origin": r.origin or "",
        "servings": r.servings,
        "duration_min": r.duration_min,
        "difficulty": r.difficulty,
        "calories": r.calories,
        "image_url": r.image_url or "",
        "images": _load_json(r.images, []),
        "moderation_status": r.moderation_status,
        "is_daily_dish": r.is_daily_dish,
        "author": author_mini(r.author),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "avg_rating": avg,
        "review_count": count,
        "saves": saves,
        # meta gata formatat pentru cardurile din frontend
        "meta": {
            "time": f"{r.duration_min} min" if r.duration_min else "",
            "servings": f"{r.servings} servings" if r.servings else "",
            "kcal": f"{r.calories} kcal" if r.calories else "",
            "level": r.difficulty or "",
        },
    }
    if full:
        data.update(
            {
                "ingredients": _load_json(r.ingredients, []),
                "steps": _load_json(r.steps, []),
                "nutrition": _load_json(r.nutrition, []),
                "allergens": _load_json(r.allergens, {"contains": [], "free": []}),
                "ai_notes": r.ai_notes or "",
            }
        )
    return data


def user_to_dict(db: Session, u: "models.User", viewer: "models.User" = None):
    followers = (
        db.query(func.count(models.Follow.id))
        .filter(models.Follow.following_id == u.id)
        .scalar()
    )
    following = (
        db.query(func.count(models.Follow.id))
        .filter(models.Follow.follower_id == u.id)
        .scalar()
    )
    recipe_count = (
        db.query(func.count(models.Recipe.id))
        .filter(models.Recipe.author_id == u.id)
        .scalar()
    )
    is_following = False
    if viewer is not None and viewer.id != u.id:
        is_following = (
            db.query(models.Follow)
            .filter(
                models.Follow.follower_id == viewer.id,
                models.Follow.following_id == u.id,
            )
            .first()
            is not None
        )
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "email": u.email if (viewer is not None and viewer.id == u.id) else None,
        "avatar_url": u.avatar_url or "",
        "bio": u.bio or "",
        "level": u.level,
        "xp_total": u.xp_total,
        "role": u.role,
        "followers": int(followers or 0),
        "following": int(following or 0),
        "recipe_count": int(recipe_count or 0),
        "is_following": is_following,
        "is_self": viewer is not None and viewer.id == u.id,
    }


def review_to_dict(db: Session, rv: "models.Review", viewer: "models.User" = None):
    return {
        "id": rv.id,
        "rating": rv.rating,
        "comment": rv.comment or "",
        "photo_url": rv.photo_url or "",
        "recipe_id": rv.recipe_id,
        "user": author_mini(rv.user),
        "created_at": rv.created_at.isoformat() if rv.created_at else None,
        "is_mine": viewer is not None and rv.user_id == viewer.id,
    }
