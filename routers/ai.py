"""Endpointuri AI care au nevoie de contextul aplicației.

Deocamdată: asistentul din cook-along. Spre deosebire de moderarea/nutriția
din `services/ai.py`, aici modelul primește rețeta întreagă plus pasul la care
a ajuns utilizatorul, ca să poată răspunde la „cât mai stă?" fără ca omul să
repete contextul.
"""
from fastapi import APIRouter, Depends, HTTPException

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user
from services import ai, ranks, visibility
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/cook/{recipe_id}")
def ask_while_cooking(
    recipe_id: int,
    data: schemas.CookAsk,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    question = (data.message or "").strip()
    if not question:
        raise HTTPException(400, "Scrie o întrebare")

    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    staff = visibility.is_staff(user)
    mine = recipe.author_id == user.id
    if recipe.moderation_status == "hidden" and not (staff or mine):
        raise HTTPException(404, "Rețeta nu există")
    if recipe.author_id in visibility.hidden_author_ids(db, user):
        raise HTTPException(404, "Rețeta nu există")

    # Aceeași poartă de rank ca la deschiderea rețetei — altfel asistentul ar
    # dicta pașii unei rețete pe care contul nu are voie s-o vadă.
    recipe_rank = ranks.normalize_recipe_rank(recipe.rank, recipe.difficulty)
    if not (staff or mine) and not ranks.can_access_recipe(user.xp_total or 0, recipe_rank):
        raise HTTPException(403, "Rețeta e peste rank-ul tău")

    payload = serializers.recipe_to_dict(db, recipe, full=True, viewer=user)
    history = [{"role": m.role, "text": m.text} for m in (data.history or [])]

    answer = ai.cook_answer(
        recipe=payload,
        step_index=max(0, data.step_index),
        question=question,
        history=history,
    )
    return {
        "text": answer["text"],
        "ok": answer["ok"],
        "step_index": data.step_index,
    }
