"""Conversie obiecte ORM -> dict pentru răspunsuri JSON.

Aici se face deserializarea câmpurilor text-JSON (ingredients, steps,
nutrition, allergens, images) și calculul câmpurilor derivate (rating mediu,
număr recenzii, urmăritori)."""
import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def _ranks():
    """Import întârziat — evită un ciclu la import între module de servicii."""
    from services import ranks
    return ranks


def iso_utc(dt):
    """ISO cu marcaj de fus orar.

    Toate datele din DB sunt scrise cu `datetime.utcnow()`, deci sunt UTC — dar
    naive. `isoformat()` pe ele produce „2026-09-02T11:43:12", fără marcaj, iar
    `new Date(...)` din browser citește un asemenea șir ca oră LOCALĂ. Pe o
    mașină la UTC+3 fiecare oră afișată ieșea cu 3 ore greșită: o rețetă publicată
    acum apărea „acum 3 ore", iar o suspendare de 24h arăta 21.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _load_json(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def _lang_name(code: str) -> str:
    """Numele afișabil al limbii sursă. Import întârziat: `services.ai` importă
    la rândul lui modele, iar serializers e încărcat foarte devreme."""
    try:
        from services import ai
        return ai.language_name(code)
    except Exception:
        return (code or "").upper()


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


def recipe_to_dict(db: Session, r: "models.Recipe", full: bool = False,
                   viewer: "models.User" = None):
    """Card (full=False) sau detaliu complet (full=True).

    `viewer` e folosit doar ca să spunem dacă rețeta e peste rank-ul lui —
    afișarea (titlu, poză, rank) rămâne vizibilă, conținutul e blocat în router.
    """
    ranks = _ranks()
    avg, count, saves = recipe_stats(db, r.id)
    rank = ranks.normalize_recipe_rank(getattr(r, "rank", ""), r.difficulty)
    rank_meta = ranks.RANK_BY_ID.get(rank, {})
    data = {
        "id": r.id,
        "title": r.title,
        "description": r.description or "",
        "origin": r.origin or "",
        "servings": r.servings,
        "duration_min": r.duration_min,
        "difficulty": r.difficulty,
        "rank": rank,
        "rank_name": rank_meta.get("name", rank.title()),
        "rank_color": rank_meta.get("vibrant", ""),
        "rank_tier": ranks.first_tier_of_rank(rank),
        # Blocarea e o decizie de produs: rețetele peste rank-ul tău nu se
        # deschid. Rămân vizibile ca listing, ca să ai ce să țintești.
        "locked": viewer is not None
        and not ranks.can_access_recipe(viewer.xp_total, rank),
        "calories": r.calories,
        "image_url": r.image_url or "",
        "images": _load_json(r.images, []),
        "moderation_status": r.moderation_status,
        # limba în care a fost scrisă original (conținutul de mai jos e engleză)
        "source_language": getattr(r, "source_language", "") or "en",
        "is_daily_dish": r.is_daily_dish,
        "author": author_mini(r.author),
        "created_at": iso_utc(r.created_at),
        "avg_rating": avg,
        "review_count": count,
        "saves": saves,
        # meta gata formatat pentru cardurile din frontend
        "meta": {
            "time": f"{r.duration_min} min" if r.duration_min else "",
            "servings": f"{r.servings} servings" if r.servings else "",
            "kcal": f"{r.calories} kcal" if r.calories else "",
            "level": rank_meta.get("name", rank.title()),
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
                "source_language_name": _lang_name(
                    getattr(r, "source_language", "") or "en"
                ),
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
    is_self = viewer is not None and viewer.id == u.id
    prefs = _load_json(getattr(u, "settings", ""), {})
    is_private = bool(prefs.get("privateAccount", False))
    data = {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "email": u.email if is_self else None,
        "avatar_url": u.avatar_url or "",
        "cover_url": getattr(u, "cover_url", "") or "",
        "bio": u.bio or "",
        # `level` rămâne pentru consumatorii vechi ai API-ului; rank-ul e sursa
        # adevărului și se calculează din xp_total, deci nu se desincronizează.
        "level": u.level,
        "xp_total": u.xp_total,
        "rank": _ranks().progress_for_xp(u.xp_total),
        "role": u.role,
        "followers": int(followers or 0),
        "following": int(following or 0),
        "recipe_count": int(recipe_count or 0),
        "is_following": is_following,
        "is_self": is_self,
        "private": is_private,
        "created_at": iso_utc(u.created_at),
    }
    # preferințele de cont sunt private — le trimitem doar posesorului
    if is_self:
        data["theme"] = u.theme or "light"
        data["language"] = u.language or "ro"
        data["units"] = u.units or "metric"
        data["settings"] = _load_json(getattr(u, "settings", ""), {})
        # Starea de sancțiune trebuie să ajungă la posesor, altfel interfața n-are
        # cum să-i spună de ce nu mai poate face nimic: în DB scria „suspendat",
        # dar /me nu raporta asta, așa că frontend-ul îl trata ca pe oricine.
        until = getattr(u, "suspended_until", None)
        suspended = bool(until and until > datetime.utcnow())
        data["suspended"] = suspended
        data["suspended_until"] = iso_utc(until) if suspended else None
        data["is_active"] = bool(u.is_active)
    return data


def _is_following(db: Session, viewer: "models.User", u: "models.User") -> bool:
    if viewer is None or viewer.id == u.id:
        return False
    return (
        db.query(models.Follow)
        .filter(models.Follow.follower_id == viewer.id, models.Follow.following_id == u.id)
        .first()
        is not None
    )


def can_view_profile(db: Session, u: "models.User", viewer: "models.User") -> bool:
    """Un profil privat e vizibil complet doar posesorului sau urmăritorilor."""
    prefs = _load_json(getattr(u, "settings", ""), {})
    if not prefs.get("privateAccount", False):
        return True
    if viewer is not None and viewer.id == u.id:
        return True
    return _is_following(db, viewer, u)


def user_public_limited(db: Session, u: "models.User", viewer: "models.User" = None):
    """Payload minim pentru un cont privat pe care nu-l urmărești: doar
    identitatea (nume + username) + coperta, ca să poți cere follow."""
    is_self = viewer is not None and viewer.id == u.id
    followers = (
        db.query(func.count(models.Follow.id))
        .filter(models.Follow.following_id == u.id)
        .scalar()
    )
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "avatar_url": u.avatar_url or "",
        "cover_url": getattr(u, "cover_url", "") or "",
        "followers": int(followers or 0),
        "private": True,
        "locked": True,
        "is_following": _is_following(db, viewer, u),
        "is_self": is_self,
    }


def review_to_dict(db: Session, rv: "models.Review", viewer: "models.User" = None,
                   with_recipe: bool = False):
    data = {
        "id": rv.id,
        "rating": rv.rating,
        "comment": rv.comment or "",
        "photo_url": rv.photo_url or "",
        "recipe_id": rv.recipe_id,
        "user": author_mini(rv.user),
        "created_at": iso_utc(rv.created_at),
        "is_mine": viewer is not None and rv.user_id == viewer.id,
    }
    if with_recipe:
        r = rv.recipe
        data["recipe"] = {
            "id": r.id,
            "title": r.title,
            "image_url": r.image_url or "",
            "origin": r.origin or "",
        } if r else None
    return data
