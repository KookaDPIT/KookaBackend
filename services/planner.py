"""Planificatorul: lista de cumpărături și calendarul de mese.

Logica stă aici, nu în router, pentru că are DOI apelanți: paginile (prin
`routers/planner.py`) și asistentul din chat, care poate adăuga ingrediente
sau poate plănui o săptămână în urma unei conversații. Ambele trebuie să
producă exact aceleași rânduri, altfel „adaugă-mi astea pe listă" ar crea
intrări pe care pagina nu le știe interpreta.
"""
import json
import re
from datetime import date, datetime, timedelta

import models

SLOTS = ("breakfast", "lunch", "dinner", "snack")
DEFAULT_SLOT = "dinner"

# Cât de departe acceptăm o planificare. Ține greșelile de tastare („2206")
# în afara calendarului fără să limiteze planificarea rezonabilă.
MAX_DAYS_AHEAD = 400
MAX_DAYS_BEHIND = 120

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# „200 g flour" / „2 onions" / „500ml milk" -> (cantitate, unitate, nume)
_AMOUNT_RE = re.compile(
    r"^\s*(?P<qty>\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)\s*"
    r"(?P<unit>kg|g|mg|l|ml|cl|dl|tbsp|tsp|cups?|cloves?|slices?|cans?|pcs?|buc)?\b\s*"
    r"(?P<name>.+)$",
    re.IGNORECASE,
)


def normalize_slot(value: str) -> str:
    value = (value or "").strip().lower()
    return value if value in SLOTS else DEFAULT_SLOT


def normalize_date(value: str) -> str:
    """Acceptă YYYY-MM-DD; orice altceva cade pe ziua de azi.

    Datele vin și de la model, care poate scrie „next Tuesday" sau o dată din
    2019. O dată invalidă nu trebuie să arunce planificarea la gunoi, dar nici
    să ajungă în DB — așa că se normalizează la azi și se prinde în fereastră.
    """
    today = date.today()
    text = (value or "").strip()
    if not _DATE_RE.match(text):
        return today.isoformat()
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return today.isoformat()
    if parsed > today + timedelta(days=MAX_DAYS_AHEAD):
        return (today + timedelta(days=MAX_DAYS_AHEAD)).isoformat()
    if parsed < today - timedelta(days=MAX_DAYS_BEHIND):
        return today.isoformat()
    return parsed.isoformat()


def split_amount(line: str):
    """Desparte o linie de ingredient în (nume, cantitate, unitate).

    Rețetele își scriu ingredientele ca text („200 g flour"), dar lista de
    cumpărături vrea cantitatea separat ca să poată fi editată. Ce nu se
    potrivește tiparului rămâne întreg ca nume — mai bine „a handful of basil"
    fără cantitate decât o cantitate inventată.
    """
    raw = (line or "").strip()
    if not raw:
        return "", "", ""
    match = _AMOUNT_RE.match(raw)
    if not match:
        return raw, "", ""
    name = (match.group("name") or "").strip(" ,.-")
    if not name:
        return raw, "", ""
    qty = (match.group("qty") or "").replace(",", ".").replace(" ", "")
    unit = (match.group("unit") or "").lower()
    return name, qty, unit


# ---------- lista de cumpărături ----------

def shopping_to_dict(item: models.ShoppingItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity or "",
        "unit": item.unit or "",
        "checked": bool(item.checked),
        "source": item.source or "manual",
        "recipe_id": item.recipe_id,
        "expires_at": getattr(item, "expires_at", "") or "",
    }


def _same_item(item: models.ShoppingItem, name: str, unit: str) -> bool:
    return (
        item.name.strip().lower() == name.strip().lower()
        and (item.unit or "").lower() == (unit or "").lower()
    )


def add_shopping(db, user, name: str, quantity="", unit="", source="manual",
                 recipe_id=None):
    """Adaugă sau adună.

    Aceeași cerere de două ori nu trebuie să dea două rânduri identice pe
    listă. Cantitățile se adună doar când ambele sunt numere cu aceeași
    unitate; altfel păstrăm rândul existent și nu inventăm o sumă.
    """
    clean = (name or "").strip()
    if not clean:
        return None
    unit = (unit or "").strip().lower()
    quantity = str(quantity or "").strip()

    existing = (
        db.query(models.ShoppingItem)
        .filter(models.ShoppingItem.user_id == user.id)
        .all()
    )
    for item in existing:
        if not _same_item(item, clean, unit):
            continue
        try:
            if quantity and item.quantity:
                item.quantity = _fmt_number(float(item.quantity) + float(quantity))
            elif quantity:
                item.quantity = quantity
        except ValueError:
            pass  # una dintre ele nu e numerică — lăsăm ce era
        item.checked = False  # a fost cerut din nou: nu mai e bifat
        return item

    item = models.ShoppingItem(
        user_id=user.id,
        name=clean,
        quantity=quantity,
        unit=unit,
        source=source,
        recipe_id=recipe_id,
    )
    db.add(item)
    return item


def _fmt_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def add_recipe_ingredients(db, user, recipe: models.Recipe, source="recipe"):
    """Trece toate ingredientele unei rețete pe listă, cu cantități separate."""
    try:
        ingredients = json.loads(recipe.ingredients or "[]")
    except (ValueError, TypeError):
        ingredients = []
    added = []
    for line in ingredients:
        if not isinstance(line, str):
            continue
        name, qty, unit = split_amount(line)
        item = add_shopping(
            db, user, name, qty, unit, source=source, recipe_id=recipe.id
        )
        if item is not None:
            added.append(item)
    return added


# ---------- calendarul de mese ----------

def meal_to_dict(db, entry: models.MealPlanEntry) -> dict:
    data = {
        "id": entry.id,
        "date": entry.date,
        "slot": entry.slot or DEFAULT_SLOT,
        "title": entry.title or "",
        "recipe_id": entry.recipe_id,
        "source": entry.source or "manual",
        "position": entry.position or 0,
        "recipe": None,
    }
    if entry.recipe_id:
        recipe = (
            db.query(models.Recipe)
            .filter(models.Recipe.id == entry.recipe_id)
            .first()
        )
        # o rețetă ștearsă între timp lasă titlul, nu un card mort
        if recipe is not None and recipe.moderation_status == "ok":
            data["recipe"] = {
                "id": recipe.id,
                "title": recipe.title,
                "image_url": recipe.image_url or "",
                "duration_min": recipe.duration_min,
                "calories": recipe.calories,
            }
            data["title"] = data["title"] or recipe.title
        else:
            data["recipe_id"] = None
    return data


def add_meal(db, user, day: str, title: str = "", recipe_id=None,
             slot=DEFAULT_SLOT, source="manual"):
    day = normalize_date(day)
    slot = normalize_slot(slot)

    recipe = None
    if recipe_id:
        recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
        if recipe is None or recipe.moderation_status != "ok":
            recipe = None
            recipe_id = None

    clean_title = (title or "").strip() or (recipe.title if recipe else "")
    if not clean_title:
        return None

    # aceeași rețetă, în aceeași zi și același moment al zilei, o singură dată
    duplicate = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.user_id == user.id,
            models.MealPlanEntry.date == day,
            models.MealPlanEntry.slot == slot,
            models.MealPlanEntry.title == clean_title,
        )
        .first()
    )
    if duplicate is not None:
        return duplicate

    used = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.user_id == user.id,
            models.MealPlanEntry.date == day,
        )
        .count()
    )
    entry = models.MealPlanEntry(
        user_id=user.id,
        date=day,
        slot=slot,
        title=clean_title,
        recipe_id=recipe_id,
        source=source,
        position=used,
    )
    db.add(entry)
    return entry


def week_bounds(anchor: str = ""):
    """Luni→duminică pentru săptămâna care conține `anchor` (implicit azi)."""
    try:
        day = date.fromisoformat(anchor) if anchor else date.today()
    except ValueError:
        day = date.today()
    monday = day - timedelta(days=day.weekday())
    return monday.isoformat(), (monday + timedelta(days=6)).isoformat()


def apply_ai_plan(db, user, plan: dict) -> dict:
    """Aplică ce a cerut asistentul și raportează ce a ieșit.

    Modelul propune; aici se decide. Tot ce intră trece prin aceleași funcții
    ca butoanele din interfață, așa că nu poate crea rânduri pe care pagina nu
    le înțelege — și rețete inexistente cad pe simplu titlu.
    """
    result = {"shopping": [], "meals": []}
    if not isinstance(plan, dict):
        return result

    for raw in (plan.get("shopping_add") or [])[:25]:
        if isinstance(raw, str):
            name, qty, unit = split_amount(raw)
        elif isinstance(raw, dict):
            name = str(raw.get("name") or "").strip()
            qty = str(raw.get("quantity") or "").strip()
            unit = str(raw.get("unit") or "").strip()
            if not qty and name:
                name, qty, unit = split_amount(name) if not unit else (name, qty, unit)
        else:
            continue
        item = add_shopping(db, user, name, qty, unit, source="ai")
        if item is not None:
            result["shopping"].append(item)

    for raw in (plan.get("meals") or [])[:21]:
        if not isinstance(raw, dict):
            continue
        entry = add_meal(
            db,
            user,
            raw.get("date") or "",
            title=str(raw.get("title") or "").strip(),
            recipe_id=raw.get("recipe_id"),
            slot=raw.get("slot") or DEFAULT_SLOT,
            source="ai",
        )
        if entry is not None:
            result["meals"].append(entry)

    if result["shopping"] or result["meals"]:
        db.flush()
    return result


def summarize_for_model(db, user) -> list:
    """Ce are omul deja pe listă și în calendar, ca asistentul să nu repete.

    Câteva linii, nu tot: fiecare se plătește în tokeni la fiecare mesaj.
    """
    lines = []
    items = (
        db.query(models.ShoppingItem)
        .filter(
            models.ShoppingItem.user_id == user.id,
            models.ShoppingItem.checked == False,  # noqa: E712
        )
        .order_by(models.ShoppingItem.created_at.desc())
        .limit(20)
        .all()
    )
    if items:
        lines.append(
            "SHOPPING LIST (already on it - do not add these again): "
            + ", ".join(
                f"{i.quantity} {i.unit} {i.name}".strip() if i.quantity else i.name
                for i in items
            )
        )

    today = date.today().isoformat()
    horizon = (date.today() + timedelta(days=10)).isoformat()
    meals = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.user_id == user.id,
            models.MealPlanEntry.date >= today,
            models.MealPlanEntry.date <= horizon,
        )
        .order_by(models.MealPlanEntry.date.asc())
        .limit(20)
        .all()
    )
    if meals:
        lines.append(
            "MEAL PLAN (already scheduled): "
            + "; ".join(f"{m.date} {m.slot}: {m.title}" for m in meals)
        )

    lines.append(f"Today is {today} ({datetime.now().strftime('%A')}).")
    return lines
