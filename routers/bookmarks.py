"""Semne de carte — lista de „vreau să gătesc asta cândva".

Calendarul (`MealPlanEntry`) răspunde la „când gătesc asta"; semnul de carte
răspunde la „poate, cândva", ceea ce e o întrebare diferită și mult mai
frecventă. Separat și de `SavedRecipe`, care e starea gătitului și se creează
singură la verificarea AI: a le îmbina ar însemna că scoaterea din listă șterge
și dovada că ai gătit rețeta.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import serializers
from database import get_db
from deps import get_current_user
from services import visibility

router = APIRouter(tags=["bookmarks"])


def _row(db: Session, user_id: int, recipe_id: int):
    return (
        db.query(models.Bookmark)
        .filter(
            models.Bookmark.user_id == user_id,
            models.Bookmark.recipe_id == recipe_id,
        )
        .first()
    )


@router.get("/me/bookmarks")
def list_bookmarks(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Rețetele marcate, cele mai noi primele.

    `ids` călătorește separat de `recipes`: interfața are nevoie de mulțimea
    completă ca să știe ce buton e apăsat pe orice card de oriunde din
    aplicație, iar rețetele ascunse între timp de un moderator (sau ale unui
    autor blocat) dispar din `recipes` fără să dispară din mulțime — altfel
    butonul ar arăta „nemarcat" pe o rețetă pe care chiar ai marcat-o și un
    al doilea clic ar da 409.
    """
    rows = (
        db.query(models.Bookmark)
        .filter(models.Bookmark.user_id == user.id)
        .order_by(models.Bookmark.created_at.desc())
        .all()
    )
    ids = [row.recipe_id for row in rows]
    if not ids:
        return {"ids": [], "recipes": []}

    hidden = visibility.hidden_author_ids(db, user)
    query = visibility.visible_authors(
        db.query(models.Recipe), models.Recipe, hidden
    ).filter(
        models.Recipe.id.in_(ids),
        models.Recipe.moderation_status == "ok",
    )
    by_id = {r.id: r for r in query.all()}
    # ordinea rămâne cea a marcării, nu cea din SQL
    recipes = [by_id[i] for i in ids if i in by_id]
    return {
        "ids": ids,
        "recipes": [serializers.recipe_to_dict(db, r, viewer=user) for r in recipes],
    }


@router.post("/recipes/{recipe_id}/bookmark", status_code=status.HTTP_201_CREATED)
def add_bookmark(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    # Idempotent: a marca de două ori e ce se întâmplă când butonul e apăsat
    # din două tab-uri, nu o eroare pe care utilizatorul s-o poată repara.
    if _row(db, user.id, recipe_id) is None:
        db.add(models.Bookmark(user_id=user.id, recipe_id=recipe_id))
        db.commit()
    return {"bookmarked": True, "recipe_id": recipe_id}


@router.delete("/recipes/{recipe_id}/bookmark")
def remove_bookmark(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    row = _row(db, user.id, recipe_id)
    if row is not None:
        db.delete(row)
        db.commit()
    return {"bookmarked": False, "recipe_id": recipe_id}
