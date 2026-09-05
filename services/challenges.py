# -*- coding: utf-8 -*-
"""Provocările zilnice.

Trei rețete pe zi, una ușoară / una medie / una grea, alese determinist pentru
data curentă și memorate în `daily_challenges` — același calcul leneș ca la
Daily Global Dish, fără scheduler. Se completează gătind rețeta și trecând
verificarea AI a pozei, iar XP-ul depinde de rank-ul rețetei.
"""
import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

import models
from services import ranks, visibility

# XP per rank de rețetă — o provocare de Platinum trebuie să conteze vizibil mai
# mult decât una de Copper, altfel nimeni nu alege greul.
XP_BY_RANK = {
    "copper": 60,
    "bronze": 90,
    "silver": 130,
    "gold": 180,
    "platinum": 240,
    "chef": 320,
}

# Fiecare slot trage dintr-un grup de rank-uri, ca să existe mereu o provocare
# accesibilă și una ambițioasă.
SLOTS = [
    {"slot": 0, "label": "easy", "ranks": ["copper", "bronze"]},
    {"slot": 1, "label": "medium", "ranks": ["silver", "gold"]},
    {"slot": 2, "label": "hard", "ranks": ["platinum", "chef"]},
]


def today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _pick(recipes: list, date: str, slot: int):
    """Alegere deterministă: aceeași zi + același slot dau mereu aceeași rețetă,
    fără să stocăm o sămânță aleatoare."""
    if not recipes:
        return None
    digest = hashlib.sha256(f"{date}:{slot}".encode()).hexdigest()
    return recipes[int(digest, 16) % len(recipes)]


def _eligible(db: Session, rank_ids: list):
    silenced = visibility.silenced_user_ids(db)
    query = (
        db.query(models.Recipe)
        .filter(models.Recipe.moderation_status == "ok")
        .filter(models.Recipe.rank.in_(rank_ids))
    )
    return [r for r in query.all() if r.author_id is None or r.author_id not in silenced]


def ensure_today(db: Session) -> list:
    """Întoarce (creând la nevoie) provocările zilei de azi."""
    date = today()
    existing = (
        db.query(models.DailyChallenge)
        .filter(models.DailyChallenge.date == date)
        .order_by(models.DailyChallenge.slot)
        .all()
    )
    if len(existing) == len(SLOTS):
        return existing

    have = {row.slot for row in existing}
    # Rezervăm rețetele deja alese azi, ca să nu iasă aceeași de două ori.
    used = {row.recipe_id for row in existing}

    for spec in SLOTS:
        if spec["slot"] in have:
            continue
        pool = [r for r in _eligible(db, spec["ranks"]) if r.id not in used]
        if not pool:
            # Catalogul nu are nimic la rank-ul cerut — sărim slotul; se va
            # completa de la sine când apar rețete potrivite.
            continue
        pool.sort(key=lambda r: r.id)
        recipe = _pick(pool, date, spec["slot"])
        if recipe is None:
            continue
        used.add(recipe.id)
        rank = ranks.normalize_recipe_rank(recipe.rank, recipe.difficulty)
        db.add(models.DailyChallenge(
            date=date,
            slot=spec["slot"],
            recipe_id=recipe.id,
            rank=rank,
            xp=XP_BY_RANK.get(rank, 60),
        ))

    db.commit()
    return (
        db.query(models.DailyChallenge)
        .filter(models.DailyChallenge.date == date)
        .order_by(models.DailyChallenge.slot)
        .all()
    )


def _done_ids(db: Session, user_id: int, challenge_ids: list) -> set:
    if not challenge_ids:
        return set()
    rows = (
        db.query(models.DailyChallengeDone.challenge_id)
        .filter(
            models.DailyChallengeDone.user_id == user_id,
            models.DailyChallengeDone.challenge_id.in_(challenge_ids),
        )
        .all()
    )
    return {row[0] for row in rows}


def list_for_user(db: Session, user) -> list:
    """Provocările de azi, cu starea lor pentru userul curent."""
    rows = ensure_today(db)
    done = _done_ids(db, user.id, [row.id for row in rows])
    labels = {spec["slot"]: spec["label"] for spec in SLOTS}
    user_tier = ranks.tier_for_xp(user.xp_total)

    out = []
    for row in rows:
        recipe = db.query(models.Recipe).filter(models.Recipe.id == row.recipe_id).first()
        if recipe is None:
            continue
        out.append({
            "id": row.id,
            "slot": row.slot,
            "label": labels.get(row.slot, ""),
            "xp": row.xp,
            "rank": row.rank,
            "rank_name": ranks.RANK_BY_ID.get(row.rank, {}).get("name", row.rank),
            "done": row.id in done,
            # Rețetele peste rank-ul tău rămân blocate și ca provocare — altfel
            # provocarea ar fi un ocol pe lângă regula de acces.
            "locked": not ranks.can_access_recipe(user.xp_total, row.rank),
            "recipe": {
                "id": recipe.id,
                "title": recipe.title,
                "image_url": recipe.image_url or "",
                "origin": recipe.origin or "",
                "duration_min": recipe.duration_min or 0,
            },
        })
    return out


def complete_for_recipe(db: Session, user, recipe_id: int):
    """Apelat după o verificare AI reușită: dacă rețeta gătită e provocarea de
    azi, o marchează terminată. Întoarce provocarea completată sau None."""
    rows = ensure_today(db)
    match = next((row for row in rows if row.recipe_id == recipe_id), None)
    if match is None:
        return None
    if _done_ids(db, user.id, [match.id]):
        return None  # deja revendicată azi
    db.add(models.DailyChallengeDone(
        user_id=user.id,
        challenge_id=match.id,
        xp_awarded=match.xp,
    ))
    return match
