"""Filtrele „inteligente" ale feed-ului de pe Home.

Trei dintre chipsuri nu se pot scrie ca WHERE: au nevoie de ingredientele și
alergenii deserializați din coloanele-JSON, sau de semnalul social al celui
care se uită. Toate primesc un lot de rețete deja filtrate de vizibilitate și
îl reordonează/îl taie în Python.

Fiecare funcție întoarce `[(recipe, extra), ...]` — `extra` sunt câmpurile în
plus pe care le lipim peste dicționarul serializat (potrivirea din frigider,
motivul recomandării), ca frontend-ul să poată explica de ce e cardul acolo.
"""
import json
import re

import models
from services import allergens as allergen_svc
from services import ranks

# Cuvinte care apar în aproape orice listă de ingrediente și n-ar trebui să
# conteze drept „potrivire" — altfel apa și sarea fac orice rețetă să pară
# gătibilă din ce ai în frigider.
_STOPWORDS = {
    "water", "salt", "pepper", "oil", "sugar", "to", "taste", "of", "and",
    "for", "the", "a", "some", "fresh", "ground", "chopped", "large", "small",
    "medium", "optional", "cup", "cups", "tbsp", "tsp", "g", "kg", "ml", "l",
    "oz", "lb", "clove", "cloves", "pinch", "handful",
}

_WORD_RE = re.compile(r"[a-z]+")


def _load(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def _words(text: str) -> set:
    return {w for w in _WORD_RE.findall((text or "").lower()) if len(w) > 2} - _STOPWORDS


def parse_pantry(raw: str) -> list:
    """„eggs, cheddar cheese, spring onion" -> [{'eggs'}, {'cheddar','cheese'}, …]"""
    out = []
    for part in (raw or "").replace("\n", ",").split(","):
        words = _words(part)
        if words:
            out.append(words)
    return out


def _user_allergies(viewer):
    return allergen_svc.parse_user(getattr(viewer, "allergies", "")) if viewer else []


def _clashes(recipe, user_keys):
    return allergen_svc.conflicts(
        user_keys, _load(recipe.allergens, {"contains": [], "free": []})
    )


# ---------- fără alergenii mei ----------

def allergy_free(pool, viewer):
    """Scoate din listă tot ce conține un alergen declarat.

    Fără alergii declarate filtrul n-are ce filtra — lăsăm lista întreagă, dar
    marcăm asta, ca interfața să poată propune completarea profilului în loc să
    arate un rezultat care pare rupt."""
    keys = _user_allergies(viewer)
    if not keys:
        return [(r, {"feed_reason": "no_allergies_set"}) for r in pool]
    out = []
    for r in pool:
        if _clashes(r, keys):
            continue
        out.append((r, {"feed_reason": "allergy_free"}))
    return out


# ---------- cu ce am în frigider ----------

# Sub atât rețeta nu e „gătibilă din ce ai", e doar înrudită.
_FRIDGE_MIN_COVER = 0.34


def fridge(pool, viewer, pantry_raw: str):
    pantry = parse_pantry(pantry_raw)
    if not pantry:
        return []

    allergy_keys = _user_allergies(viewer)
    scored = []
    for r in pool:
        ingredients = _load(r.ingredients, [])
        if not ingredients:
            continue
        have, missing = 0, []
        for line in ingredients:
            line_words = _words(line if isinstance(line, str) else str(line))
            if any(item & line_words for item in pantry):
                have += 1
            else:
                missing.append(line)
        cover = have / len(ingredients)
        if cover < _FRIDGE_MIN_COVER:
            continue
        scored.append((
            r,
            {
                "feed_reason": "fridge",
                "match_percent": round(cover * 100),
                "have_count": have,
                "need_count": len(ingredients),
                # doar câteva: lista completă e pe pagina rețetei
                "missing": missing[:4],
                "allergen_warning": bool(_clashes(r, allergy_keys)),
            },
        ))
    # cea mai bună acoperire prima; la egalitate, mai puține ingrediente
    scored.sort(key=lambda x: (-x[1]["match_percent"], x[1]["need_count"]))
    return scored


# ---------- recomandat pentru tine ----------

def recommended(db, pool, viewer):
    """Un scor simplu și explicabil, nu un model.

    Contează, în ordinea greutății: autorii pe care îi urmărești, bucătăriile
    din care ai gătit deja, rank-ul potrivit (ce e blocat coboară, nu dispare —
    trebuie să ai ce ținti), nota medie și prospețimea. Ce conține un alergen
    declarat iese complet.
    """
    if viewer is None:
        return [(r, {"feed_reason": "fresh"}) for r in pool]

    followed = {
        row[0]
        for row in db.query(models.Follow.following_id)
        .filter(models.Follow.follower_id == viewer.id)
        .all()
    }
    cooked_origins = {
        (row[0] or "").strip().lower()
        for row in db.query(models.Recipe.origin)
        .join(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(
            models.SavedRecipe.user_id == viewer.id,
            models.SavedRecipe.cooked_verified == True,  # noqa: E712
        )
        .all()
        if (row[0] or "").strip()
    }
    rated = {
        row[0]: row[1]
        for row in db.query(models.Review.recipe_id, models.Review.rating)
        .filter(models.Review.user_id == viewer.id)
        .all()
    }
    allergy_keys = _user_allergies(viewer)
    viewer_tier = ranks.tier_for_xp(viewer.xp_total or 0)

    scored = []
    for r in pool:
        if _clashes(r, allergy_keys):
            continue
        if r.id in rated:
            continue  # deja gătită și notată — nu i-o mai propunem

        score = 0.0
        reason = "fresh"
        if r.author_id in followed:
            score += 4.0
            reason = "followed_author"
        origin = (r.origin or "").strip().lower()
        if origin and origin in cooked_origins:
            score += 2.5
            if reason == "fresh":
                reason = "same_cuisine"

        rank = ranks.normalize_recipe_rank(getattr(r, "rank", ""), r.difficulty)
        gap = viewer_tier - ranks.first_tier_of_rank(rank)
        if gap < 0:
            score -= 3.0            # peste rank: rămâne, dar la coadă
        elif gap <= 2:
            score += 1.5            # exact la nivelul tău
            if reason == "fresh":
                reason = "your_rank"

        avg, count, _ = _stats(db, r.id)
        score += min(avg, 5) * 0.4 + min(count, 20) * 0.05
        if r.author_id == viewer.id:
            score -= 1.5            # propriile rețete nu sunt o descoperire

        scored.append((score, r, {"feed_reason": reason}))

    scored.sort(key=lambda x: (-x[0], -(x[1].id or 0)))
    return [(r, extra) for _, r, extra in scored]


def _stats(db, recipe_id):
    from serializers import recipe_stats
    return recipe_stats(db, recipe_id)


def apply_smart_filter(db, pool, name: str, viewer, pantry_raw: str = ""):
    if name == "fridge":
        return fridge(pool, viewer, pantry_raw)
    if name == "allergy_free":
        return allergy_free(pool, viewer)
    if name == "recommended":
        return recommended(db, pool, viewer)
    return [(r, {}) for r in pool]
