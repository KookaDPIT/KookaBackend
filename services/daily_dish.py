"""Algoritmul Daily Global Dish.

Calcul lazy pe zi (fără scheduler): la prima cerere din ziua curentă alegem o
rețetă bine cotată/populară, evitând rețetele și țările featured recent, și
salvăm alegerea în tabelul daily_dishes pentru idempotență."""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from services import visibility

RECENT_RECIPE_DAYS = 14   # nu repeta aceeași rețetă în ultimele 2 săptămâni
RECENT_ORIGIN_DAYS = 3    # preferă o țară diferită față de ultimele 3 zile


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _is_eligible(db: Session, recipe) -> bool:
    """Publicată și cu autor nesuspendat. O rețetă ascunsă de moderator sau al
    cărei autor a fost suspendat nu mai are ce căuta pe prima pagină."""
    if recipe is None or recipe.moderation_status != "ok":
        return False
    if recipe.author_id is None:
        return True
    return recipe.author_id not in visibility.silenced_user_ids(db)


def _score_query(db: Session):
    """Rețete 'ok' ordonate după rating mediu, apoi nr. recenzii, apoi salvări."""
    avg_rating = func.coalesce(func.avg(models.Review.rating), 0).label("avg_rating")
    review_count = func.count(func.distinct(models.Review.id)).label("review_count")
    save_count = func.count(func.distinct(models.SavedRecipe.id)).label("save_count")
    return (
        db.query(
            models.Recipe.id,
            models.Recipe.origin,
            models.Recipe.author_id,
            avg_rating,
            review_count,
            save_count,
        )
        .outerjoin(models.Review, models.Review.recipe_id == models.Recipe.id)
        .outerjoin(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(models.Recipe.moderation_status == "ok")
        .group_by(models.Recipe.id, models.Recipe.origin, models.Recipe.author_id)
        .order_by(avg_rating.desc(), review_count.desc(), save_count.desc(),
                  models.Recipe.id.desc())
    )


def get_or_pick_daily(db: Session):
    """Întoarce Recipe pentru ziua curentă (o creează dacă nu există). None dacă
    nu există nicio rețetă în DB."""
    today = _today()

    existing = (
        db.query(models.DailyDish).filter(models.DailyDish.date == today).first()
    )
    if existing:
        recipe = (
            db.query(models.Recipe)
            .filter(models.Recipe.id == existing.recipe_id)
            .first()
        )
        if _is_eligible(db, recipe):
            return recipe
        # Ștearsă, ascunsă de moderator sau autor suspendat între timp. Alegem
        # alta, dar păstrăm rândul de azi: felul zilei se schimbă o singură dată
        # și rămâne stabil până la miezul nopții, nu la fiecare cerere.
        if recipe is not None:
            recipe.is_daily_dish = False
        db.delete(existing)
        db.commit()

    # rețete featured recent (de evitat)
    recent_cutoff = (datetime.utcnow() - timedelta(days=RECENT_RECIPE_DAYS)).strftime("%Y-%m-%d")
    recent_recipe_ids = {
        d.recipe_id
        for d in db.query(models.DailyDish)
        .filter(models.DailyDish.date >= recent_cutoff)
        .all()
    }
    # țări featured în ultimele zile (de evitat dacă se poate)
    origin_cutoff = (datetime.utcnow() - timedelta(days=RECENT_ORIGIN_DAYS)).strftime("%Y-%m-%d")
    recent_origin_dish_ids = [
        d.recipe_id
        for d in db.query(models.DailyDish)
        .filter(models.DailyDish.date >= origin_cutoff)
        .all()
    ]
    recent_origins = {
        (r.origin or "").lower()
        for r in db.query(models.Recipe)
        .filter(models.Recipe.id.in_(recent_origin_dish_ids))
        .all()
    } if recent_origin_dish_ids else set()

    silenced = visibility.silenced_user_ids(db)
    ranked = [
        row for row in _score_query(db).all()
        if row.author_id is None or row.author_id not in silenced
    ]
    if not ranked:
        return None

    def pick(candidates):
        return candidates[0] if candidates else None

    # 1) nu recent + țară diferită
    chosen = pick([
        row for row in ranked
        if row.id not in recent_recipe_ids
        and (row.origin or "").lower() not in recent_origins
    ])
    # 2) doar nu recent (relaxăm țara)
    if chosen is None:
        chosen = pick([row for row in ranked if row.id not in recent_recipe_ids])
    # 3) orice (DB mică)
    if chosen is None:
        chosen = ranked[0]

    recipe = db.query(models.Recipe).filter(models.Recipe.id == chosen.id).first()

    # marcăm ziua + flag pe rețetă
    db.query(models.Recipe).filter(models.Recipe.is_daily_dish == True).update(
        {models.Recipe.is_daily_dish: False}
    )
    recipe.is_daily_dish = True
    db.add(models.DailyDish(date=today, recipe_id=recipe.id))
    db.commit()
    db.refresh(recipe)
    return recipe
