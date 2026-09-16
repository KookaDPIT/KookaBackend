"""Utilizatori: /me, profil public, urmărire (follow) și pașaport culinar."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

import json

import auth
import models
import schemas
import serializers
from serializers import iso_utc
from database import get_db
from deps import get_current_user, get_current_user_optional
from services import allergens as allergen_svc
from services import streaks as streak_svc
from services import trophies as trophy_svc
from services import visibility

router = APIRouter(tags=["users"])


def _load_settings(user) -> dict:
    try:
        return json.loads(user.settings or "{}") or {}
    except (ValueError, TypeError):
        return {}


def _dismissed_activity(user) -> set:
    """Intrările pe care posesorul le-a scos din propria activitate. Stocate în
    blobul de preferințe, nu într-un tabel: e o alegere de afișare, nu date —
    iar ascunderea nu trebuie să șteargă rețeta sau recenzia de dedesubt."""
    raw = _load_settings(user).get("hiddenActivity")
    return set(raw) if isinstance(raw, list) else set()


@router.get("/allergens")
def allergen_catalog():
    """Vocabularul de alergeni pe care îl bifezi la înregistrare și în setări.
    Trimis de backend ca lista să fie una singură pe ambele capete."""
    return {"allergens": allergen_svc.table()}


@router.get("/me")
def me(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return serializers.user_to_dict(db, user, viewer=user)


@router.patch("/me")
def update_me(
    data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    payload = data.model_dump(exclude_none=True)

    # username/email sunt unice — verifică să nu fie deja luate de alt cont
    new_username = payload.get("username")
    if new_username is not None:
        new_username = new_username.strip().lstrip("@")
        if not new_username:
            raise HTTPException(400, "Numele de utilizator nu poate fi gol")
        taken = (
            db.query(models.User)
            .filter(models.User.username == new_username, models.User.id != user.id)
            .first()
        )
        if taken:
            raise HTTPException(400, "Numele de utilizator este deja folosit")
        payload["username"] = new_username

    new_email = payload.get("email")
    if new_email is not None:
        new_email = new_email.strip()
        if not new_email:
            raise HTTPException(400, "Emailul nu poate fi gol")
        taken = (
            db.query(models.User)
            .filter(models.User.email == new_email, models.User.id != user.id)
            .first()
        )
        if taken:
            raise HTTPException(400, "Emailul este deja folosit")
        payload["email"] = new_email

    # Alergiile vin fie ca listă bifată, fie ca șir vechi separat prin virgulă;
    # coloana stochează întotdeauna cheile canonice, ca filtrarea să nu depindă
    # de cum a scris cineva „tree nuts".
    if "allergies" in payload:
        raw = payload["allergies"]
        values = raw if isinstance(raw, list) else str(raw).split(",")
        payload["allergies"] = allergen_svc.serialize_user(values)

    for field, value in payload.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return serializers.user_to_dict(db, user, viewer=user)


@router.patch("/me/password")
def change_password(
    data: schemas.PasswordChange,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not auth.verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, "Parola curentă este incorectă")
    user.hashed_password = auth.hash_password(data.new_password)
    db.commit()
    return {"ok": True}


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    # suspendat / dezactivat / blocat → 404 și pe URL direct, nu doar în listări
    if not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    # cont privat pe care nu-l urmărești → doar identitatea (nume + username)
    if not serializers.can_view_profile(db, u, viewer):
        return serializers.user_public_limited(db, u, viewer)
    return serializers.user_to_dict(db, u, viewer=viewer)


@router.get("/users/{user_id}/recipes")
def user_recipes(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return []
    recipes = (
        db.query(models.Recipe)
        .filter(
            models.Recipe.author_id == user_id,
            models.Recipe.moderation_status == "ok",
        )
        .order_by(models.Recipe.created_at.desc())
        .all()
    )
    return [serializers.recipe_to_dict(db, r) for r in recipes]


@router.get("/users/{user_id}/activity")
def user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Activitate recentă compusă din: rețete publicate, recenzii scrise și
    preparate gătite-verificate. Respectă confidențialitatea profilului."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return []

    dismissed = _dismissed_activity(u)
    items = []

    authored = (
        db.query(models.Recipe)
        .filter(models.Recipe.author_id == user_id, models.Recipe.moderation_status == "ok")
        .order_by(models.Recipe.created_at.desc())
        .limit(10)
        .all()
    )
    for r in authored:
        if f"created:{r.id}" in dismissed:
            continue
        items.append({
            "kind": "created",
            "what": r.title,
            "recipe_id": r.id,
            "entry_id": r.id,
            "when": iso_utc(r.created_at),
        })

    reviews = (
        db.query(models.Review)
        .filter(models.Review.user_id == user_id)
        .order_by(models.Review.created_at.desc())
        .limit(10)
        .all()
    )
    for rv in reviews:
        # o rețetă ștearsă sau ascunsă nu mai are ce căuta în activitate
        if rv.recipe is None or rv.recipe.moderation_status != "ok":
            continue
        if f"reviewed:{rv.id}" in dismissed:
            continue
        items.append({
            "kind": "reviewed",
            "what": rv.recipe.title,
            "recipe_id": rv.recipe_id,
            "entry_id": rv.id,
            "when": iso_utc(rv.created_at),
        })

    cooked = (
        db.query(models.SavedRecipe)
        .join(models.Recipe, models.Recipe.id == models.SavedRecipe.recipe_id)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.cooked_verified == True,
        )
        .order_by(models.SavedRecipe.created_at.desc())
        .limit(10)
        .all()
    )
    for sv in cooked:
        recipe = db.query(models.Recipe).filter(models.Recipe.id == sv.recipe_id).first()
        if recipe is None or recipe.moderation_status != "ok":
            continue
        if f"cooked:{sv.id}" in dismissed:
            continue
        items.append({
            "kind": "cooked",
            "what": recipe.title,
            "recipe_id": sv.recipe_id,
            "entry_id": sv.id,
            "when": iso_utc(sv.created_at),
        })

    # cele mai noi primele; punem la coadă cele fără dată
    items.sort(key=lambda x: x["when"] or "", reverse=True)
    return items[:15]


@router.post("/users/{user_id}/follow", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if user_id == user.id:
        raise HTTPException(400, "Nu te poți urmări pe tine")
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "Utilizatorul nu există")

    existing = (
        db.query(models.Follow)
        .filter(
            models.Follow.follower_id == user.id,
            models.Follow.following_id == user_id,
        )
        .first()
    )
    if not existing:
        db.add(models.Follow(follower_id=user.id, following_id=user_id))
        db.commit()
    return {"following": True}


@router.delete("/users/{user_id}/follow")
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Follow).filter(
        models.Follow.follower_id == user.id,
        models.Follow.following_id == user_id,
    ).delete()
    db.commit()
    return {"following": False}


@router.get("/users/{user_id}/followers")
def followers(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.User)
        .join(models.Follow, models.Follow.follower_id == models.User.id)
        .filter(models.Follow.following_id == user_id)
        .all()
    )
    return [serializers.user_to_dict(db, u, viewer) for u in rows]


@router.get("/users/{user_id}/following")
def following(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.User)
        .join(models.Follow, models.Follow.following_id == models.User.id)
        .filter(models.Follow.follower_id == user_id)
        .all()
    )
    return [serializers.user_to_dict(db, u, viewer) for u in rows]


@router.get("/users/{user_id}/passport")
def passport(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Țări distincte din rețetele autorate + rețetele gătite-verificate."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return {"countries": [], "total": 0}
    counts = {}

    authored = (
        db.query(models.Recipe.origin)
        .filter(
            models.Recipe.author_id == user_id,
            models.Recipe.origin != "",
            models.Recipe.moderation_status == "ok",
        )
        .all()
    )
    for (origin,) in authored:
        key = origin.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1

    cooked = (
        db.query(models.Recipe.origin)
        .join(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.cooked_verified == True,
            models.Recipe.origin != "",
            models.Recipe.moderation_status == "ok",
        )
        .all()
    )
    for (origin,) in cooked:
        key = origin.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1

    countries = [{"country": k, "count": v} for k, v in sorted(counts.items())]
    return {"countries": countries, "total": len(countries)}


@router.get("/users/{user_id}/passport/{country}")
def passport_country(
    user_id: int,
    country: str,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Ce anume a adus ștampila: rețetele publicate și cele gătite din țara asta."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return {"country": country, "recipes": []}

    code = country.strip()
    items = []
    seen = set()

    authored = (
        db.query(models.Recipe)
        .filter(
            models.Recipe.author_id == user_id,
            func.lower(models.Recipe.origin) == code.lower(),
            models.Recipe.moderation_status == "ok",
        )
        .order_by(models.Recipe.created_at.desc())
        .all()
    )
    for r in authored:
        seen.add(r.id)
        items.append({**serializers.recipe_to_dict(db, r), "how": "created"})

    cooked = (
        db.query(models.Recipe, models.SavedRecipe.created_at)
        .join(models.SavedRecipe, models.SavedRecipe.recipe_id == models.Recipe.id)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.cooked_verified == True,
            func.lower(models.Recipe.origin) == code.lower(),
            models.Recipe.moderation_status == "ok",
        )
        .order_by(models.SavedRecipe.created_at.desc())
        .all()
    )
    for r, cooked_at in cooked:
        if r.id in seen:
            # publicată ȘI gătită de același om — o singură intrare, cea mai tare
            for item in items:
                if item["id"] == r.id:
                    item["how"] = "both"
                    item["cooked_at"] = iso_utc(cooked_at)
            continue
        seen.add(r.id)
        items.append({
            **serializers.recipe_to_dict(db, r),
            "how": "cooked",
            "cooked_at": iso_utc(cooked_at),
        })

    return {"country": code, "recipes": items, "total": len(items)}


# ---------- activitatea proprie: ascunde / repune ----------

@router.post("/me/activity/hide")
def hide_activity(
    data: schemas.ActivityRef,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    prefs = _load_settings(user)
    hidden = set(prefs.get("hiddenActivity") or [])
    hidden.add(f"{data.kind}:{data.entry_id}")
    prefs["hiddenActivity"] = sorted(hidden)
    user.settings = json.dumps(prefs, ensure_ascii=False)
    db.commit()
    return {"hidden": sorted(hidden)}


@router.delete("/me/activity/hide")
def unhide_all_activity(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    prefs = _load_settings(user)
    prefs["hiddenActivity"] = []
    user.settings = json.dumps(prefs, ensure_ascii=False)
    db.commit()
    return {"hidden": []}


# ---------- streak-uri ----------

@router.get("/me/streaks")
def my_streaks(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Cele patru streak-uri ale userului curent.

    Endpoint separat de /me pentru că se calculează din istoric (trei interogări
    peste tabele de evenimente), iar /me e cerut la fiecare încărcare de pagină.
    """
    return streak_svc.for_user(db, user)


@router.get("/users/{user_id}/streaks")
def user_streaks(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Aceleași streak-uri, pe profilul public — sub aceleași reguli de
    confidențialitate ca restul profilului."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        raise HTTPException(403, "Profil privat")
    return streak_svc.for_user(db, u)


# ---------- trofee ----------

@router.get("/me/trophies")
def my_trophies(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Toate trofeele cu starea lor, plus totalurile pe categorii.

    Cele ascunse pe care nu le ai vin cu numele și descrierea golite — asta e
    tot rostul lor, iar dacă textul ar circula prin API oricine ar putea citi
    lista din DevTools.
    """
    return trophy_svc.evaluate(db, user)


@router.get("/users/{user_id}/trophies")
def user_trophies(
    user_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u or not visibility.can_see_user(db, u, viewer):
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        raise HTTPException(403, "Profil privat")
    return trophy_svc.evaluate(db, u)


# ---------- blocări ----------

@router.get("/me/blocked")
def list_blocked(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    rows = (
        db.query(models.User)
        .join(models.Block, models.Block.blocked_id == models.User.id)
        .filter(models.Block.blocker_id == user.id)
        .all()
    )
    return [serializers.author_mini(u) for u in rows]


@router.post("/users/{user_id}/block", status_code=status.HTTP_201_CREATED)
def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if user_id == user.id:
        raise HTTPException(400, "Nu te poți bloca pe tine")
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "Utilizatorul nu există")

    existing = (
        db.query(models.Block)
        .filter(models.Block.blocker_id == user.id, models.Block.blocked_id == user_id)
        .first()
    )
    if not existing:
        db.add(models.Block(blocker_id=user.id, blocked_id=user_id))
    # blocarea rupe și legătura de urmărire, în ambele sensuri
    db.query(models.Follow).filter(
        or_(
            and_(models.Follow.follower_id == user.id, models.Follow.following_id == user_id),
            and_(models.Follow.follower_id == user_id, models.Follow.following_id == user.id),
        )
    ).delete(synchronize_session=False)
    db.commit()
    return {"blocked": True}


@router.delete("/users/{user_id}/block")
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Block).filter(
        models.Block.blocker_id == user.id,
        models.Block.blocked_id == user_id,
    ).delete()
    db.commit()
    return {"blocked": False}


# ---------- clasamente ----------

def _leaderboard_row(db: Session, u: models.User, position: int, viewer):
    from services import ranks

    return {
        "position": position,
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "avatar_url": u.avatar_url or "",
        "xp_total": int(u.xp_total or 0),
        "rank": ranks.progress_for_xp(u.xp_total),
        "role": u.role,
        "is_self": viewer is not None and u.id == viewer.id,
    }


def _mutual_follow_ids(db: Session, user_id: int) -> set:
    """„Prietenii" = follow reciproc. Cine te-a urmărit înapoi, nu oricine
    urmărești: altfel clasamentul „cu prietenii" ar fi o listă pe care ți-o
    poți umple singur."""
    following = {
        row[0]
        for row in db.query(models.Follow.following_id)
        .filter(models.Follow.follower_id == user_id)
        .all()
    }
    if not following:
        return set()
    followers = {
        row[0]
        for row in db.query(models.Follow.follower_id)
        .filter(models.Follow.following_id == user_id)
        .all()
    }
    return following & followers


@router.get("/leaderboard")
def leaderboard(
    scope: str = "global",
    limit: int = 50,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user),
):
    """Clasamentul după XP — global sau doar între prieteni.

    Poziția proprie se întoarce întotdeauna, chiar dacă e în afara paginii
    afișate: întrebarea „pe ce loc sunt?" trebuie să aibă răspuns și de pe
    locul 900.
    """
    limit = max(1, min(int(limit or 50), 100))
    scope = "friends" if scope == "friends" else "global"

    query = db.query(models.User).filter(models.User.is_active == True)  # noqa: E712
    # conturile sancționate nu figurează în clasament cât ține sancțiunea
    query = query.filter(
        or_(
            models.User.suspended_until == None,  # noqa: E711
            models.User.suspended_until <= func.now(),
        )
    )

    if scope == "friends":
        friends = _mutual_follow_ids(db, viewer.id)
        friends.add(viewer.id)
        query = query.filter(models.User.id.in_(friends))

    rows = query.order_by(
        models.User.xp_total.desc(), models.User.created_at.asc()
    ).all()

    # blocările sunt simetrice: cine te-a blocat (sau invers) nu apare
    hidden = visibility.hidden_author_ids(db, viewer)
    rows = [u for u in rows if u.id not in hidden or u.id == viewer.id]

    entries = [_leaderboard_row(db, u, i + 1, viewer) for i, u in enumerate(rows)]
    me_entry = next((e for e in entries if e["is_self"]), None)

    return {
        "scope": scope,
        "total": len(entries),
        "entries": entries[:limit],
        "me": me_entry,
    }
