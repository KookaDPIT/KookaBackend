"""Recenzii + verificarea AI că ai gătit rețeta.

Regula: poți lăsa recenzie doar după ce ai marcat rețeta ca gătită ȘI AI-ul a
confirmat poza (cooked_verified). Îți poți edita/șterge propria recenzie."""
import base64
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user, get_current_user_optional
from services import ai, challenges, learn, ranks, visibility

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
async def verify_cook(
    recipe_id: int,
    session_id: int = Query(0, description="sesiunea de cook-along, pentru trofee"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Verifică poza de gătit cu AI-ul FĂRĂ a o stoca nicăieri.

    Imaginea e trimisă lui Groq ca data-URI base64 (efemer, în memorie) și apoi
    aruncată — nu ajunge pe ImageKit, iar `cook_photo_url` rămâne gol."""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Fișier gol")
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(400, "Imaginea depășește 8 MB")

    mime = file.content_type or "image/jpeg"
    data_uri = f"data:{mime};base64,{base64.b64encode(content).decode()}"

    result = ai.verify_cook(title=recipe.title, image_url=data_uri)

    saved = _saved(db, user.id, recipe_id)
    if not saved:
        saved = models.SavedRecipe(user_id=user.id, recipe_id=recipe_id)
        db.add(saved)
    saved.cooked = True
    saved.cook_photo_url = ""  # dovada NU se păstrează
    saved.cooked_verified = bool(result["verified"])

    response = {
        "verified": bool(result["verified"]),
        "reason": result["reason"],
        "can_review": bool(result["verified"]),
    }

    # Închiderea sesiunii de cook-along. O poză respinsă nu o termină — poți
    # încerca alta — dar se numără: „AI-ul ți-a comentat farfuria" e un trofeu.
    session = None
    if session_id:
        session = (
            db.query(models.CookSession)
            .filter(
                models.CookSession.id == session_id,
                models.CookSession.user_id == user.id,
            )
            .first()
        )
    if session is not None:
        if result["verified"]:
            session.finished_at = datetime.utcnow()
            # Ai terminat-o: un abandon de mai devreme din ACEEAȘI sesiune nu
            # mai e un abandon, e o pauză.
            session.gave_up_at = None
        else:
            session.verify_failures = (session.verify_failures or 0) + 1

    if result["verified"]:
        saved.cooked_at = datetime.utcnow()

        # XP-ul urmează rank-ul rețetei, nu o valoare fixă: 25 pentru Copper,
        # 150 pentru Chef (services/ranks.COOK_XP_BY_RANK). Reluările primesc un
        # sfert — vezi comentariul de acolo pentru de ce nu zero și nu tot.
        recipe_rank = ranks.normalize_recipe_rank(recipe.rank, recipe.difficulty)
        times_cooked = 1 + (
            db.query(models.CookLog)
            .filter(
                models.CookLog.user_id == user.id,
                models.CookLog.recipe_id == recipe_id,
            )
            .count()
        )
        cook_xp = ranks.cook_xp(recipe_rank, times_cooked)
        gained = cook_xp

        # Istoricul e separat de SavedRecipe, care păstrează doar ultima gătire:
        # streak-urile și trofeele au nevoie de fiecare dată în parte.
        db.add(models.CookLog(
            user_id=user.id,
            recipe_id=recipe_id,
            rank=recipe_rank,
            xp_awarded=cook_xp,
            times_cooked=times_cooked,
            cooked_at=saved.cooked_at,
        ))
        response["cook_xp"] = cook_xp
        response["cook_rank"] = recipe_rank
        response["times_cooked"] = times_cooked

        # O gătire confirmată poate încheia o provocare a zilei…
        challenge = challenges.complete_for_recipe(db, user, recipe_id)
        if challenge is not None:
            gained += challenge.xp
            response["challenge_completed"] = {"id": challenge.id, "xp": challenge.xp}

        # …și poate acorda mastery pe lecțiile unde quiz-ul avansat e deja
        # trecut și lipsea doar dovada practică.
        pending = (
            db.query(models.LessonProgress)
            .filter(
                models.LessonProgress.user_id == user.id,
                models.LessonProgress.mastery_passed.is_(True),
                models.LessonProgress.mastered.is_(False),
                models.LessonProgress.completed.is_(True),
            )
            .all()
        )
        mastered_now = []
        for progress in pending:
            # Dovada trebuie să fie ulterioară terminării lecției.
            if progress.completed_at and saved.cooked_at < progress.completed_at:
                continue
            lesson = db.query(models.Lesson).filter(
                models.Lesson.id == progress.lesson_id
            ).first()
            if lesson is None:
                continue
            progress.mastered = True
            progress.mastered_at = saved.cooked_at
            gained += lesson.mastery_xp or 0
            mastered_now.append(lesson.title)
        if mastered_now:
            response["mastered"] = mastered_now

        response.update(learn.award_xp(user, gained))

    db.commit()
    return response


@router.get("/reviews/recent")
def recent_reviews(
    limit: int = 8,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Cele mai recente recenzii din toată aplicația, cu info despre rețetă
    (pentru secțiunea „Fresh reviews" de pe Home)."""
    # Blocarea trebuie să taie și recenziile, nu doar rețetele și postările:
    # altfel blochezi pe cineva și îl citești în continuare pe prima pagină.
    hidden = visibility.hidden_author_ids(db, viewer)
    query = db.query(models.Review)
    if hidden:
        query = query.filter(models.Review.user_id.notin_(hidden))
    reviews = (
        query.order_by(models.Review.created_at.desc())
        .limit(min(limit, 30))
        .all()
    )
    return [serializers.review_to_dict(db, r, viewer, with_recipe=True) for r in reviews]


@router.get("/recipes/{recipe_id}/reviews")
def list_reviews(
    recipe_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    hidden = visibility.hidden_author_ids(db, viewer)
    review_query = db.query(models.Review).filter(models.Review.recipe_id == recipe_id)
    if hidden:
        review_query = review_query.filter(models.Review.user_id.notin_(hidden))
    reviews = review_query.order_by(models.Review.created_at.desc()).all()
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
