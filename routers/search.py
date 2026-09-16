"""Căutare globală: rețete (nume/țară) + utilizatori (username/nume)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import serializers
from database import get_db
from deps import get_current_user_optional
from services import courses, visibility

router = APIRouter(tags=["search"])


@router.get("/courses")
def course_vocabulary():
    """Vocabularul închis al tipurilor de fel + mesele la care se potrivesc.

    Cerut o singură dată de frontend, ca butoanele de filtru să vină din aceeași
    listă pe care o folosesc analizorul și validarea — nu dintr-o copie care
    apucă să se desincronizeze.
    """
    return {"courses": courses.table(), "meals": courses.MEALS}


@router.get("/search")
def search(
    q: str = Query("", min_length=0),
    course: str = Query("", description="tipuri de fel, separate prin virgulă"),
    meal: str = Query("", description="breakfast|lunch|dinner|snack"),
    kcal_min: int = Query(0, ge=0),
    kcal_max: int = Query(0, ge=0, description="0 = fără plafon"),
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    q = q.strip()
    faceted = bool(course or meal or kcal_min or kcal_max)
    # „Nimic de căutat" înseamnă acum text gol ȘI fără filtre: „arată-mi toate
    # deserturile sub 400 kcal" e o căutare validă fără niciun cuvânt în ea.
    if not q and not faceted:
        return {"recipes": [], "users": []}

    hidden = visibility.hidden_author_ids(db, viewer)

    recipes = visibility.visible_authors(
        db.query(models.Recipe), models.Recipe, hidden
    )
    recipes = recipes.filter(models.Recipe.moderation_status == "ok")
    if q:
        like = f"%{q.lower()}%"
        recipes = recipes.filter(
            or_(
                func.lower(models.Recipe.title).like(like),
                func.lower(models.Recipe.origin).like(like),
            )
        )
    recipes = courses.apply_facets(recipes, models.Recipe, course, meal, kcal_min, kcal_max)
    recipes = (
        recipes
        .order_by(models.Recipe.created_at.desc())
        .limit(40 if faceted else 20)
        .all()
    )

    # Oamenii se caută doar după nume. Filtrele de mai sus sunt despre mâncare,
    # deci o căutare care are doar filtre nu are cum să returneze utilizatori.
    if not q:
        return {
            "recipes": [serializers.recipe_to_dict(db, r, viewer=viewer) for r in recipes],
            "users": [],
        }

    like = f"%{q.lower()}%"
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
