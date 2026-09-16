"""Rețete: creare (cu analiză AI), listare/filtrare, detaliu, editare, ștergere."""
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user, get_current_user_optional
from services import ai, courses, feed, ranks, visibility

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_recipe(
    data: schemas.RecipeCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not data.title.strip():
        raise HTTPException(400, "Titlul e obligatoriu")
    if not data.ingredients:
        raise HTTPException(400, "Adaugă cel puțin un ingredient")
    if not data.steps:
        raise HTTPException(400, "Adaugă cel puțin un pas")

    steps = [s.model_dump(exclude_none=True) for s in data.steps]

    # ---- traducere: site-ul e în engleză, autorul poate scrie în limba lui ----
    # Ce ajunge în DB e mereu engleza; `source_language` reține originalul.
    tr = ai.translate_recipe(
        title=data.title,
        description=data.description,
        ingredients=data.ingredients,
        steps=steps,
    )
    title = tr["title"].strip()
    description = tr["description"]
    ingredients = tr["ingredients"]
    steps = tr["steps"]

    # Ce a scris autorul, exact cum a scris. Se păstrează doar când chiar s-a
    # tradus: pentru o rețetă deja în engleză ar fi o a doua copie identică.
    original = (
        {
            "title": data.title.strip(),
            "description": data.description or "",
            "ingredients": json.dumps(list(data.ingredients), ensure_ascii=False),
            "steps": json.dumps(
                [s.model_dump(exclude_none=True) for s in data.steps], ensure_ascii=False
            ),
        }
        if tr["translated"]
        else {"title": "", "description": "", "ingredients": "", "steps": ""}
    )

    # ---- analiză AI: nutriție + moderare (pe textul deja în engleză) ----
    analysis = ai.analyze_recipe(
        title=title,
        ingredients=ingredients,
        steps=steps,
        servings=data.servings,
    )

    if not analysis["valid"]:
        # conținut clar invalid -> respinge
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rețeta a fost respinsă de verificarea AI: {analysis['reason']}",
        )

    recipe = models.Recipe(
        title=title,
        description=description,
        origin=data.origin,
        servings=data.servings,
        duration_min=data.duration_min,
        difficulty=data.difficulty,
        rank=ranks.normalize_recipe_rank(data.rank, data.difficulty),
        # Ce alege autorul are prioritate; analizorul completează când n-a ales
        # nimic, iar euristica din titlu e ultima plasă.
        course=(
            courses.normalize(getattr(data, "course", ""))
            or courses.normalize(analysis.get("course", ""))
            or courses.guess(title, ingredients, description)
        ),
        ingredients=json.dumps(ingredients, ensure_ascii=False),
        steps=json.dumps(steps, ensure_ascii=False),
        source_language=tr["language"],
        original_title=original["title"],
        original_description=original["description"],
        original_ingredients=original["ingredients"],
        original_steps=original["steps"],
        nutrition=json.dumps(analysis["nutrition"], ensure_ascii=False),
        allergens=json.dumps(analysis["allergens"], ensure_ascii=False),
        calories=analysis["calories"],
        image_url=data.image_url,
        images=json.dumps(data.images, ensure_ascii=False),
        moderation_status="ok",
        ai_notes=analysis.get("reason", ""),
        author_id=user.id,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    # XP pentru publicarea unei rețete
    user.xp_total = (user.xp_total or 0) + 50
    db.commit()

    return serializers.recipe_to_dict(db, recipe, full=True)


# Filtrele care nu se pot exprima în SQL (au nevoie de ingredientele și
# alergenii deserializați, sau de semnalul social al celui care se uită) se
# rezolvă în Python peste un lot mai mare decât pagina cerută.
_SMART_FILTERS = {"recommended", "fridge", "allergy_free"}
_SMART_POOL = 240


@router.get("")
def list_recipes(
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
    q: str = Query("", description="căutare titlu/țară"),
    filter: str = Query(
        "", description="recommended|under30|fridge|allergy_free|top_rated|random"
    ),
    pantry: str = Query("", description="ingrediente din frigider, separate prin virgulă"),
    course: str = Query("", description="tipuri de fel, separate prin virgulă (services/courses)"),
    meal: str = Query("", description="breakfast|lunch|dinner|snack"),
    kcal_min: int = Query(0, ge=0, description="kcal per porție, minim"),
    kcal_max: int = Query(0, ge=0, description="kcal per porție, maxim (0 = fără plafon)"),
    limit: int = Query(20, le=100),
    offset: int = 0,
):
    query = db.query(models.Recipe).filter(models.Recipe.moderation_status == "ok")
    query = visibility.visible_authors(
        query, models.Recipe, visibility.hidden_author_ids(db, viewer)
    )

    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Recipe.title).like(like),
                func.lower(models.Recipe.origin).like(like),
            )
        )

    query = courses.apply_facets(query, models.Recipe, course, meal, kcal_min, kcal_max)

    if filter == "under30":
        query = query.filter(models.Recipe.duration_min <= 30, models.Recipe.duration_min > 0)

    if filter == "random":
        # `func.random()` există și pe Postgres, și pe SQLite; `func.rand()`
        # (MySQL) nu ne interesează. E plasa de siguranță a feed-ului: mai bine
        # câteva rețete la întâmplare decât un ecran gol.
        query = query.order_by(func.random())
    elif filter == "top_rated":
        # ordonăm după rating mediu
        avg = func.coalesce(func.avg(models.Review.rating), 0)
        query = (
            query.outerjoin(models.Review, models.Review.recipe_id == models.Recipe.id)
            .group_by(models.Recipe.id)
            .order_by(avg.desc(), models.Recipe.created_at.desc())
        )
    else:
        query = query.order_by(models.Recipe.created_at.desc())

    if filter in _SMART_FILTERS:
        pool = query.limit(_SMART_POOL).all()
        ranked = feed.apply_smart_filter(db, pool, filter, viewer, pantry)
        page = ranked[offset : offset + limit]
        return [
            {**serializers.recipe_to_dict(db, r, viewer=viewer), **extra}
            for r, extra in page
        ]

    recipes = query.offset(offset).limit(limit).all()
    return [serializers.recipe_to_dict(db, r, viewer=viewer) for r in recipes]


@router.get("/{recipe_id}")
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    staff = visibility.is_staff(viewer)
    mine = viewer is not None and recipe.author_id == viewer.id
    # ascunsă de moderator: doar autorul și echipa o mai pot deschide
    if recipe.moderation_status == "hidden" and not (staff or mine):
        raise HTTPException(404, "Rețeta nu există")
    # autor suspendat/blocat: 404, nu 403 — un 403 ar confirma că există
    if recipe.author_id in visibility.hidden_author_ids(db, viewer):
        raise HTTPException(404, "Rețeta nu există")

    # Rank: o rețetă peste rank-ul tău se deschide și se poate găti. Blocarea
    # dură (403) însemna că nici nu vedeai ce ai de câștigat gătind mai mult,
    # iar o rețetă „prea grea" nu e periculoasă — e doar mai grea. Trimitem
    # totuși ce rank cere, ca interfața să te întrebe „ești sigur?" la Gătește.
    recipe_rank = ranks.normalize_recipe_rank(recipe.rank, recipe.difficulty)
    # Deliberat fără excepția pentru moderatori: asta nu mai e o permisiune, e
    # o atenționare despre dificultate, iar dificultatea nu ține de rol. Doar
    # autorul e scutit — el știe ce a scris.
    above_rank = not mine and not ranks.can_access_recipe(
        viewer.xp_total if viewer else 0, recipe_rank
    )

    data = serializers.recipe_to_dict(db, recipe, full=True, viewer=viewer)
    data["can_moderate"] = staff
    data["is_hidden"] = recipe.moderation_status == "hidden"
    data["above_rank"] = above_rank
    if above_rank:
        data["rank_warning"] = {
            "required_rank": recipe_rank,
            "required_rank_name": ranks.RANK_BY_ID.get(recipe_rank, {}).get(
                "name", recipe_rank
            ),
            "your_rank": ranks.progress_for_xp(viewer.xp_total if viewer else 0),
        }
    return data


@router.put("/{recipe_id}")
def update_recipe(
    recipe_id: int,
    data: schemas.RecipeUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    if recipe.author_id != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(403, "Nu poți edita această rețetă")

    payload = data.model_dump(exclude_none=True)
    recompute = False
    for field in ("title", "description", "origin", "servings", "duration_min", "difficulty"):
        if field in payload:
            setattr(recipe, field, payload[field])
    # Rank-ul se normalizează întotdeauna: o valoare invalidă cade pe maparea
    # din dificultate, în loc să scrie gunoi în coloană.
    if "rank" in payload or "difficulty" in payload:
        recipe.rank = ranks.normalize_recipe_rank(
            payload.get("rank", recipe.rank), recipe.difficulty
        )
    # Un curs invalid nu suprascrie unul bun: mai bine rămâne ce era decât să
    # dispară rețeta din filtrul în care stătea.
    if "course" in payload:
        picked = courses.normalize(payload["course"])
        if picked:
            recipe.course = picked
    if "image_url" in payload:
        recipe.image_url = payload["image_url"]
    if "images" in payload:
        recipe.images = json.dumps(payload["images"], ensure_ascii=False)
    if "ingredients" in payload:
        recipe.ingredients = json.dumps(payload["ingredients"], ensure_ascii=False)
        recompute = True
    if "steps" in payload:
        steps = [s if isinstance(s, dict) else s for s in payload["steps"]]
        recipe.steps = json.dumps(steps, ensure_ascii=False)
        recompute = True

    # Editarea poate introduce text într-o altă limbă (sau poate readuce rețeta
    # la engleză), deci retraducem ori de câte ori s-a atins conținutul.
    if recompute or "title" in payload or "description" in payload:
        # Ce e în `recipe` acum e ce a trimis autorul la editare, deci e
        # originalul — îl reținem ÎNAINTE de a-l suprascrie cu traducerea.
        was = {
            "title": recipe.title,
            "description": recipe.description or "",
            "ingredients": recipe.ingredients or "[]",
            "steps": recipe.steps or "[]",
        }
        tr = ai.translate_recipe(
            title=recipe.title,
            description=recipe.description or "",
            ingredients=json.loads(recipe.ingredients or "[]"),
            steps=json.loads(recipe.steps or "[]"),
        )
        recipe.title = tr["title"].strip() or recipe.title
        recipe.description = tr["description"]
        recipe.ingredients = json.dumps(tr["ingredients"], ensure_ascii=False)
        recipe.steps = json.dumps(tr["steps"], ensure_ascii=False)
        recipe.source_language = tr["language"]
        if tr["translated"]:
            recipe.original_title = was["title"]
            recipe.original_description = was["description"]
            recipe.original_ingredients = was["ingredients"]
            recipe.original_steps = was["steps"]
        else:
            # Editată înapoi în engleză: golim originalul, altfel butonul ar
            # oferi „vezi originalul" și ar arăta textul de acum două versiuni.
            recipe.original_title = ""
            recipe.original_description = ""
            recipe.original_ingredients = ""
            recipe.original_steps = ""
        recompute = True

    if recompute:
        analysis = ai.analyze_recipe(
            title=recipe.title,
            ingredients=json.loads(recipe.ingredients or "[]"),
            steps=json.loads(recipe.steps or "[]"),
            servings=recipe.servings,
        )
        if analysis["valid"]:
            recipe.nutrition = json.dumps(analysis["nutrition"], ensure_ascii=False)
            recipe.allergens = json.dumps(analysis["allergens"], ensure_ascii=False)
            recipe.calories = analysis["calories"]

    db.commit()
    db.refresh(recipe)
    return serializers.recipe_to_dict(db, recipe, full=True)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    if recipe.author_id != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(403, "Nu poți șterge această rețetă")

    # aceleași curățări ca pe calea de moderare: recenziile, salvările și
    # rezervările de „felul zilei" trebuie să plece odată cu rețeta, altfel
    # rămân fantome în activitatea și pașaportul altor conturi
    db.query(models.Review).filter(models.Review.recipe_id == recipe.id).delete()
    db.query(models.SavedRecipe).filter(models.SavedRecipe.recipe_id == recipe.id).delete()
    db.query(models.DailyDish).filter(models.DailyDish.recipe_id == recipe.id).delete()
    db.delete(recipe)
    db.commit()


# ---------- moderare direct de pe pagina rețetei ----------

@router.post("/{recipe_id}/moderate")
def moderate_recipe(
    recipe_id: int,
    data: schemas.ModerationAction,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Ascunde / repune o rețetă fără ocolul prin consola de moderare — un
    moderator care tocmai a dat peste ea trebuie s-o poată trata pe loc."""
    if not visibility.is_staff(user):
        raise HTTPException(403, "Necesită drepturi de moderator")
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    if data.action == "hide":
        recipe.moderation_status = "hidden"
    elif data.action == "restore":
        recipe.moderation_status = "ok"
    else:
        raise HTTPException(400, "Acțiune invalidă")
    db.commit()
    return {"moderation_status": recipe.moderation_status}
