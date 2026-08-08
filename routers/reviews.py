"""Recenzii + verificarea AI că ai gătit rețeta.

Regula: poți lăsa recenzie doar după ce ai marcat rețeta ca gătită ȘI AI-ul a
confirmat poza (cooked_verified). Îți poți edita/șterge propria recenzie."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user, get_current_user_optional
from services import ai

router = APIRouter(tags=["reviews"])


def _saved(db: Session, user_id: int, recipe_id: int):
    return (
        db.query(models.SavedRecipe)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.recipe_id == recipe_id,
        )
        .first()
    )


@router.post("/recipes/{recipe_id}/cook/verify")
def verify_cook(
    recipe_id: int,
    data: schemas.CookVerifyRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    result = ai.verify_cook(title=recipe.title, image_url=data.cook_photo_url)

    saved = _saved(db, user.id, recipe_id)
    if not saved:
        saved = models.SavedRecipe(user_id=user.id, recipe_id=recipe_id)
        db.add(saved)
    saved.cooked = True
    saved.cook_photo_url = data.cook_photo_url
    saved.cooked_verified = bool(result["verified"])

    if result["verified"]:
        user.xp_total = (user.xp_total or 0) + 20  # XP pentru gătit

    db.commit()
    return {
        "verified": bool(result["verified"]),
        "reason": result["reason"],
        "can_review": bool(result["verified"]),
    }


@router.get("/recipes/{recipe_id}/reviews")
def list_reviews(
    recipe_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    reviews = (
        db.query(models.Review)
        .filter(models.Review.recipe_id == recipe_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
    avg, count, _ = serializers.recipe_stats(db, recipe_id)
    can_review = False
    my_review = None
    if viewer:
        saved = _saved(db, viewer.id, recipe_id)
        can_review = bool(saved and saved.cooked_verified)
        mine = (
            db.query(models.Review)
            .filter(
                models.Review.recipe_id == recipe_id,
                models.Review.user_id == viewer.id,
            )
            .first()
        )
        my_review = serializers.review_to_dict(db, mine, viewer) if mine else None
    return {
        "avg_rating": avg,
        "count": count,
        "can_review": can_review,
        "my_review": my_review,
        "items": [serializers.review_to_dict(db, r, viewer) for r in reviews],
    }


@router.post("/recipes/{recipe_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(
    recipe_id: int,
    data: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    saved = _saved(db, user.id, recipe_id)
    if not (saved and saved.cooked_verified):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Poți lăsa recenzie doar după ce ai gătit rețeta și AI-ul a confirmat poza",
        )

    existing = (
        db.query(models.Review)
        .filter(models.Review.recipe_id == recipe_id, models.Review.user_id == user.id)
        .first()
    )
    if existing:
        raise HTTPException(409, "Ai lăsat deja o recenzie. Editeaz-o pe cea existentă.")

    review = models.Review(
        rating=data.rating,
        comment=data.comment,
        photo_url=data.photo_url,
        user_id=user.id,
        recipe_id=recipe_id,
    )
    db.add(review)
    user.xp_total = (user.xp_total or 0) + 10
    db.commit()
    db.refresh(review)
    return serializers.review_to_dict(db, review, user)


@router.put("/reviews/{review_id}")
def update_review(
    review_id: int,
    data: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(404, "Recenzia nu există")
    if review.user_id != user.id:
        raise HTTPException(403, "Nu poți edita această recenzie")

    payload = data.model_dump(exclude_none=True)
    for field in ("rating", "comment", "photo_url"):
        if field in payload:
            setattr(review, field, payload[field])
    db.commit()
    db.refresh(review)
    return serializers.review_to_dict(db, review, user)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(404, "Recenzia nu există")
    if review.user_id != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(403, "Nu poți șterge această recenzie")
    db.delete(review)
    db.commit()
