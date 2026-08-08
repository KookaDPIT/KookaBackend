"""Daily Global Dish."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import serializers
from database import get_db
from services import daily_dish

router = APIRouter(tags=["daily"])


@router.get("/daily-dish")
def daily(db: Session = Depends(get_db)):
    recipe = daily_dish.get_or_pick_daily(db)
    if recipe is None:
        return {"daily": None}
    return {"daily": serializers.recipe_to_dict(db, recipe, full=True)}
