"""Moderare: listare rețete flagged, ștergere rețetă, dezactivare utilizator."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import serializers
from database import get_db
from deps import get_current_admin

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
