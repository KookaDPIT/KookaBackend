"""Moderare: rețete flagged, ștergere/ascundere rețetă, și uneltele de roluri
(listare utilizatori, schimbare rol, suspendare, activare/dezactivare)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import ROLE_LEVELS, get_current_admin, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/recipes")
def list_for_moderation(
    status_filter: str = Query("flagged", alias="status"),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipes = (
        db.query(models.Recipe)
        .filter(models.Recipe.moderation_status == status_filter)
        .order_by(models.Recipe.created_at.desc())
        .all()
    )
    return [serializers.recipe_to_dict(db, r, full=True) for r in recipes]


@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    db.delete(recipe)
    db.commit()
    return {"deleted": True}


@router.post("/recipes/{recipe_id}/hide")
def hide_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    recipe.moderation_status = "hidden"
    db.commit()
    return {"hidden": True}


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.role == "admin":
        raise HTTPException(403, "Nu poți dezactiva un admin")
    u.is_active = False
    db.commit()
    return {"deactivated": True}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    u.is_active = True
    db.commit()
    return {"activated": True}


# ==========================================================================
#  UNELTELE DE ROLURI
#  Listarea și suspendarea sunt pentru moderatori; schimbarea rolului doar
#  pentru admini (require_role("admin")), ca un moderator să nu se poată
#  auto-promova.
# ==========================================================================

def _admin_user_dict(u: models.User):
    """Vedere de moderare a unui cont: include câmpurile pe care serializatorul
    public le ascunde (email, rol, stare, suspendare)."""
    suspended = bool(u.suspended_until and u.suspended_until > datetime.utcnow())
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name or "",
        "email": u.email,
        "avatar_url": u.avatar_url or "",
        "role": u.role or "user",
        "is_active": bool(u.is_active),
        "suspended": suspended,
        "suspended_until": u.suspended_until.isoformat() if u.suspended_until else None,
        "level": u.level,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/users")
def list_users(
    q: str = Query("", description="caută după username, nume sau email"),
    role: str = Query("", description="filtrează după rol"),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    query = db.query(models.User)

    term = q.strip().lower()
    if term:
        like = f"%{term}%"
        query = query.filter(
            or_(
                func.lower(models.User.username).like(like),
                func.lower(models.User.full_name).like(like),
                func.lower(models.User.email).like(like),
            )
        )
    if role.strip():
        query = query.filter(models.User.role == role.strip())

    rows = query.order_by(models.User.created_at.desc()).limit(100).all()
    return [_admin_user_dict(u) for u in rows]


@router.patch("/users/{user_id}/role")
def set_role(
    user_id: int,
    data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    role = data.role.strip().lower()
    if role not in ROLE_LEVELS:
        raise HTTPException(400, f"Rol invalid. Alege dintre: {', '.join(ROLE_LEVELS)}")

    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.id == admin.id:
        raise HTTPException(400, "Nu-ți poți schimba propriul rol")

    u.role = role
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    data: schemas.SuspendRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Suspendare temporară: contul rămâne activ (poate citi), dar rutele care
    folosesc deps.require_not_suspended îi refuză scrierea până la termen."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.id == admin.id:
        raise HTTPException(400, "Nu te poți suspenda pe tine")
    if ROLE_LEVELS.get(u.role, 0) >= ROLE_LEVELS.get(admin.role, 0):
        raise HTTPException(403, "Nu poți suspenda un cont cu rol egal sau superior")

    u.suspended_until = datetime.utcnow() + timedelta(days=data.days)
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)


@router.delete("/users/{user_id}/suspend")
def unsuspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    u.suspended_until = None
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)
