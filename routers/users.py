"""Utilizatori: /me, profil public, urmărire (follow) și pașaport culinar."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import auth
import models
import schemas
import serializers
from database import get_db
from deps import get_current_user, get_current_user_optional

router = APIRouter(tags=["users"])


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
    if not u:
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
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return []

    items = []

    authored = (
        db.query(models.Recipe)
        .filter(models.Recipe.author_id == user_id, models.Recipe.moderation_status == "ok")
        .order_by(models.Recipe.created_at.desc())
        .limit(10)
        .all()
    )
    for r in authored:
        items.append({
            "kind": "created",
            "what": r.title,
            "recipe_id": r.id,
            "when": r.created_at.isoformat() if r.created_at else None,
        })

    reviews = (
        db.query(models.Review)
        .filter(models.Review.user_id == user_id)
        .order_by(models.Review.created_at.desc())
        .limit(10)
        .all()
    )
    for rv in reviews:
        items.append({
            "kind": "reviewed",
            "what": rv.recipe.title if rv.recipe else "",
            "recipe_id": rv.recipe_id,
            "when": rv.created_at.isoformat() if rv.created_at else None,
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
    for s in cooked:
        recipe = db.query(models.Recipe).filter(models.Recipe.id == s.recipe_id).first()
        items.append({
            "kind": "cooked",
            "what": recipe.title if recipe else "",
            "recipe_id": s.recipe_id,
            "when": s.created_at.isoformat() if s.created_at else None,
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
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if not serializers.can_view_profile(db, u, viewer):
        return {"countries": [], "total": 0}
    counts = {}

    authored = (
        db.query(models.Recipe.origin)
        .filter(models.Recipe.author_id == user_id, models.Recipe.origin != "")
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
        )
        .all()
    )
    for (origin,) in cooked:
        key = origin.strip()
        if key:
            counts[key] = counts.get(key, 0) + 1

    countries = [{"country": k, "count": v} for k, v in sorted(counts.items())]
    return {"countries": countries, "total": len(countries)}
