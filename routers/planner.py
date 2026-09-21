"""Lista de cumpărături și calendarul de mese.

Amândouă trăiau în localStorage, deci existau numai în browserul în care le
scriseseși: adăugai ingredientele de pe telefon și pe laptop lista era goală,
iar ștergerea datelor de site le pierdea. Acum sunt rânduri legate de cont.

Logica de adăugare stă în `services/planner.py` pentru că asistentul din chat
scrie prin exact aceleași funcții — vezi `routers/ai.py`.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from deps import get_current_user
from services import planner

router = APIRouter(prefix="/planner", tags=["planner"])


def _clean_expiry(value) -> str:
    """„YYYY-MM-DD" sau gol. Orice altceva e refuzat.

    Valoarea vine dintr-un OCR de pe ambalaj, deci poate fi orice; o stocăm ca
    text, dar tot ce intră trebuie să fie o dată reală, altfel lista ar afișa
    „expiră pe 2026-13-45"."""
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        date.fromisoformat(text)
    except ValueError:
        raise HTTPException(400, "Data de expirare trebuie să fie YYYY-MM-DD")
    return text


# ==========================================================================
# LISTA DE CUMPĂRĂTURI
# ==========================================================================

@router.get("/shopping")
def list_shopping(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    items = (
        db.query(models.ShoppingItem)
        .filter(models.ShoppingItem.user_id == user.id)
        # nebifate întâi: în magazin te uiți la ce mai ai de luat
        .order_by(models.ShoppingItem.checked.asc(), models.ShoppingItem.created_at.asc())
        .all()
    )
    return [planner.shopping_to_dict(i) for i in items]


@router.post("/shopping", status_code=status.HTTP_201_CREATED)
def add_shopping_item(
    data: schemas.ShoppingItemIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = planner.add_shopping(
        db, user, data.name, data.quantity or "", data.unit or ""
    )
    if item is None:
        raise HTTPException(400, "Scrie ce trebuie cumpărat")
    # `add_shopping` poate întoarce un rând existent (a adunat cantitățile). O
    # dată proaspăt scanată bate ce era acolo; una goală nu șterge nimic.
    expiry = _clean_expiry(data.expires_at)
    if expiry:
        item.expires_at = expiry
    db.commit()
    db.refresh(item)
    return planner.shopping_to_dict(item)


@router.patch("/shopping/{item_id}")
def update_shopping_item(
    item_id: int,
    data: schemas.ShoppingItemUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Editează o linie — cantitatea, unitatea, numele, sau bifarea ei.

    Cantitatea se putea doar șterge și readăuga; acum se poate corecta pe loc,
    ceea ce e ce faci de fapt în fața raftului.
    """
    item = (
        db.query(models.ShoppingItem)
        .filter(
            models.ShoppingItem.id == item_id,
            models.ShoppingItem.user_id == user.id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(404, "Linia nu există")

    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        clean = payload["name"].strip()
        if not clean:
            raise HTTPException(400, "Numele nu poate fi gol")
        item.name = clean
    if "quantity" in payload:
        item.quantity = str(payload["quantity"]).strip()
    if "unit" in payload:
        item.unit = str(payload["unit"]).strip().lower()
    if "checked" in payload:
        item.checked = bool(payload["checked"])
    if "expires_at" in payload:
        # Șirul gol e o valoare validă aici: așa se șterge o dată citită greșit.
        item.expires_at = _clean_expiry(payload["expires_at"])

    db.commit()
    db.refresh(item)
    return planner.shopping_to_dict(item)


@router.delete("/shopping/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.ShoppingItem).filter(
        models.ShoppingItem.id == item_id,
        models.ShoppingItem.user_id == user.id,
    ).delete()
    db.commit()


@router.delete("/shopping", status_code=status.HTTP_204_NO_CONTENT)
def clear_shopping(
    checked_only: bool = Query(True, description="doar liniile bifate"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.user_id == user.id
    )
    if checked_only:
        query = query.filter(models.ShoppingItem.checked == True)  # noqa: E712
    query.delete(synchronize_session=False)
    db.commit()


@router.post("/shopping/from-recipe/{recipe_id}", status_code=status.HTTP_201_CREATED)
def add_recipe_to_shopping(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Toate ingredientele unei rețete, cu cantitățile despărțite de nume."""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if recipe is None or recipe.moderation_status != "ok":
        raise HTTPException(404, "Rețeta nu există")
    added = planner.add_recipe_ingredients(db, user, recipe)
    db.commit()
    return {"added": len(added), "items": [planner.shopping_to_dict(i) for i in added]}


# ==========================================================================
# CALENDARUL DE MESE
# ==========================================================================

@router.get("/meals")
def list_meals(
    start: str = Query("", description="YYYY-MM-DD inclusiv"),
    end: str = Query("", description="YYYY-MM-DD inclusiv"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Mesele dintr-un interval. Fără interval: săptămâna curentă."""
    if not start or not end:
        start, end = planner.week_bounds(start)
    entries = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.user_id == user.id,
            models.MealPlanEntry.date >= start,
            models.MealPlanEntry.date <= end,
        )
        .order_by(
            models.MealPlanEntry.date.asc(),
            models.MealPlanEntry.position.asc(),
            models.MealPlanEntry.id.asc(),
        )
        .all()
    )
    return {
        "start": start,
        "end": end,
        "entries": [planner.meal_to_dict(db, e) for e in entries],
    }


@router.post("/meals", status_code=status.HTTP_201_CREATED)
def add_meal(
    data: schemas.MealPlanIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    entry = planner.add_meal(
        db,
        user,
        data.date,
        title=data.title or "",
        recipe_id=data.recipe_id,
        slot=data.slot or planner.DEFAULT_SLOT,
    )
    if entry is None:
        raise HTTPException(400, "Spune ce anume gătești")
    db.commit()
    db.refresh(entry)
    return planner.meal_to_dict(db, entry)


@router.patch("/meals/{entry_id}")
def update_meal(
    entry_id: int,
    data: schemas.MealPlanUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    entry = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.id == entry_id,
            models.MealPlanEntry.user_id == user.id,
        )
        .first()
    )
    if entry is None:
        raise HTTPException(404, "Masa nu există")

    payload = data.model_dump(exclude_none=True)
    if "title" in payload:
        clean = payload["title"].strip()
        if not clean:
            raise HTTPException(400, "Titlul nu poate fi gol")
        entry.title = clean
    if "date" in payload:
        entry.date = planner.normalize_date(payload["date"])
    if "slot" in payload:
        entry.slot = planner.normalize_slot(payload["slot"])

    db.commit()
    db.refresh(entry)
    return planner.meal_to_dict(db, entry)


@router.delete("/meals/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    entry_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.MealPlanEntry).filter(
        models.MealPlanEntry.id == entry_id,
        models.MealPlanEntry.user_id == user.id,
    ).delete()
    db.commit()


@router.post("/meals/{entry_id}/shopping", status_code=status.HTTP_201_CREATED)
def meal_to_shopping(
    entry_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Trece ingredientele unei mese planificate pe lista de cumpărături —
    legătura evidentă dintre cele două panouri, care lipsea."""
    entry = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.id == entry_id,
            models.MealPlanEntry.user_id == user.id,
        )
        .first()
    )
    if entry is None:
        raise HTTPException(404, "Masa nu există")
    if not entry.recipe_id:
        raise HTTPException(400, "Masa asta nu e legată de o rețetă din aplicație")

    recipe = db.query(models.Recipe).filter(models.Recipe.id == entry.recipe_id).first()
    if recipe is None:
        raise HTTPException(404, "Rețeta nu mai există")
    added = planner.add_recipe_ingredients(db, user, recipe)
    db.commit()
    return {"added": len(added), "items": [planner.shopping_to_dict(i) for i in added]}
