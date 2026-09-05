# -*- coding: utf-8 -*-
"""Learn: fagurele de lecții, quiz-urile și provocările zilnice.

Corectarea quiz-urilor se face exclusiv aici. Endpoint-urile de citire nu
trimit niciodată indexul răspunsului corect, așa că un quiz nu poate fi trecut
citind răspunsul din DevTools.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import deps
import models
from database import get_db
from schemas import QuizSubmit
from services import challenges, learn, ranks

router = APIRouter(prefix="/learn", tags=["learn"])


def _lesson_or_404(db: Session, slug: str) -> models.Lesson:
    lesson = db.query(models.Lesson).filter(models.Lesson.slug == slug).first()
    if lesson is None:
        raise HTTPException(404, "Lecția nu există")
    return lesson


@router.get("")
def get_tree(
    db: Session = Depends(get_db),
    user: models.User = Depends(deps.get_current_user),
):
    """Fagurele complet + rank-ul userului + provocările zilei."""
    data = learn.build_tree(db, user)
    data["challenges"] = challenges.list_for_user(db, user)
    return data


@router.get("/ranks")
def rank_table():
    """Tabelul celor 16 trepte — public, folosit și pentru insignele de rețetă."""
    return {"tiers": ranks.table(), "ranks": ranks.RANKS}


@router.get("/lessons/{slug}")
def get_lesson(
    slug: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(deps.get_current_user),
):
    return learn.lesson_detail(db, user, _lesson_or_404(db, slug))


@router.post("/lessons/{slug}/quiz")
def submit_quiz(
    slug: str,
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    user: models.User = Depends(deps.require_not_suspended),
):
    """Quiz-ul de trecere. 100% corect îl termină; orice greșeală pune lecția în
    cooldown 24 de ore."""
    lesson = _lesson_or_404(db, slug)
    progress = learn.get_or_create_progress(db, user.id, lesson.id)

    if progress.completed:
        raise HTTPException(400, "Lecția e deja terminată")

    detail = learn.lesson_detail(db, user, lesson)
    if detail["state"] == "locked":
        raise HTTPException(
            403,
            "Lecția e blocată: mai ai nevoie de rank"
            if detail["lock_reason"] == "rank"
            else "Termină întâi lecțiile care o deblochează",
        )
    if progress.cooldown_until and progress.cooldown_until > datetime.utcnow():
        raise HTTPException(429, "Lecția e în cooldown după un quiz ratat")

    correct, total = learn.score_answers(lesson.quiz, payload.answers)
    progress.attempts = (progress.attempts or 0) + 1
    progress.quiz_score = correct
    passed = total > 0 and correct == total

    result = {"passed": passed, "score": correct, "total": total}

    if passed:
        progress.completed = True
        progress.completed_at = datetime.utcnow()
        progress.cooldown_until = None
        result.update(learn.award_xp(user, lesson.xp or 0))
        db.commit()
        # Recalculăm arborele: o lecție terminată (sau un rank nou) poate
        # debloca alte hexagoane, iar interfața le anunță imediat.
        tree = learn.build_tree(db, user)
        result["unlocked"] = [
            node["title"] for node in tree["lessons"]
            if node["state"] == "available" and lesson.slug in node["prereqs"]
        ]
        result["tree"] = tree
        return result

    progress.cooldown_until = learn.cooldown_from_now()
    db.commit()
    result["cooldown_until"] = progress.cooldown_until.isoformat() + "Z"
    return result


@router.post("/lessons/{slug}/mastery")
def submit_mastery(
    slug: str,
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    user: models.User = Depends(deps.require_not_suspended),
):
    """Quiz-ul avansat. Trecerea lui NU dă mastery singură — mai trebuie și o
    rețetă gătită confirmată de AI după terminarea lecției."""
    lesson = _lesson_or_404(db, slug)
    progress = learn.get_or_create_progress(db, user.id, lesson.id)

    if not progress.completed:
        raise HTTPException(400, "Termină întâi lecția")
    if progress.mastered:
        raise HTTPException(400, "Lecția e deja stăpânită")

    detail = learn.lesson_detail(db, user, lesson)
    mastery = detail["mastery"]
    if not mastery["rank_ok"]:
        raise HTTPException(403, f"Quiz-ul avansat cere {mastery['req_tier_label']}")
    if progress.mastery_cooldown_until and progress.mastery_cooldown_until > datetime.utcnow():
        raise HTTPException(429, "Quiz-ul avansat e în cooldown")

    correct, total = learn.score_answers(lesson.mastery_quiz, payload.answers)
    progress.mastery_attempts = (progress.mastery_attempts or 0) + 1
    passed = total > 0 and correct == total

    result = {"passed": passed, "score": correct, "total": total}

    if not passed:
        progress.mastery_cooldown_until = learn.cooldown_from_now()
        db.commit()
        result["cooldown_until"] = progress.mastery_cooldown_until.isoformat() + "Z"
        return result

    progress.mastery_passed = True
    progress.mastery_cooldown_until = None
    result["cook_done"] = mastery["cook_done"]

    if mastery["cook_done"]:
        progress.mastered = True
        progress.mastered_at = datetime.utcnow()
        result.update(learn.award_xp(user, lesson.mastery_xp or 0))
        result["mastered"] = True
    else:
        # Quiz-ul rămâne trecut; mastery-ul se acordă la următoarea gătire
        # confirmată (vezi routers.reviews.verify_cook).
        result["mastered"] = False

    db.commit()
    result["tree"] = learn.build_tree(db, user)
    return result


@router.get("/challenges")
def get_challenges(
    db: Session = Depends(get_db),
    user: models.User = Depends(deps.get_current_user),
):
    return {"date": challenges.today(), "challenges": challenges.list_for_user(db, user)}
