"""Algoritmul Daily Global Dish.

Calcul lazy pe zi (fără scheduler): la prima cerere din ziua curentă alegem o
rețetă bine cotată/populară, evitând rețetele și țările featured recent, și
salvăm alegerea în tabelul daily_dishes pentru idempotență."""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

import models

RECENT_RECIPE_DAYS = 14   # nu repeta aceeași rețetă în ultimele 2 săptămâni
RECENT_ORIGIN_DAYS = 3    # preferă o țară diferită față de ultimele 3 zile


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _score_query(db: Session):
    """Rețete 'ok' ordonate după rating mediu, apoi nr. recenzii, apoi salvări."""
    avg_rating = func.coalesce(func.avg(models.Review.rating), 0).label("avg_rating")
    review_count = func.count(func.distinct(models.Review.id)).label("review_count")
    save_count = func.count(func.distinct(models.SavedRecipe.id)).label("save_count")
    return (
        db.query(
            models.Recipe.id,
            models.Recipe.origin,
            avg_rating,
            review_count,
            save_count,
        )
        .outerjoin(models.Review, models.Review.recipe_id == models.Recipe.id)
        .outerjoin(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(models.Recipe.moderation_status == "ok")
        .group_by(models.Recipe.id, models.Recipe.origin)
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
        if recipe:
            return recipe
        # rețeta a fost ștearsă între timp -> re-alegem
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

    ranked = _score_query(db).all()
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
