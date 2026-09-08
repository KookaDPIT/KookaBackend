"""Endpointuri AI care au nevoie de contextul aplicației.

Două lucruri diferite trăiesc aici:

* **cook-along** (`/ai/cook/{recipe_id}`) — modelul primește o singură rețetă
  și pasul exact la care a ajuns omul, ca să răspundă la „cât mai stă?" fără
  ca el să repete contextul.
* **chat liber** (`/ai/chat`) — conversație cu istoric salvat în DB. Modelul
  primește catalogul de rețete la care userul chiar are acces, așa că poate
  recomanda rețete reale din aplicație, nu inventate.

Moderarea și nutriția de la crearea rețetei stau tot în `services/ai.py`, dar
nu au nevoie de rută proprie — rulează în fluxul rețetelor.
"""
import base64
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user
from services import ai, ranks, visibility

router = APIRouter(prefix="/ai", tags=["ai"])

# O poză trimisă în chat: ajunge la model ca data-URI efemer și NU se stochează.
MAX_IMAGE_BYTES = 8 * 1024 * 1024
# Câte rețete îi arătăm modelului ca să aibă din ce alege.
CATALOGUE_LIMIT = 60


# ==========================================================================
# COOK-ALONG
# ==========================================================================

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


# ==========================================================================
# CHAT LIBER
# ==========================================================================

def _accessible_recipes(db: Session, user: models.User):
    """Rețetele pe care userul chiar le poate deschide, ca material pentru
    recomandări. Aceleași filtre ca la listare, plus poarta de rank — n-are
    rost să-i recomandăm ceva ce se lovește de un 403 la click."""
    q = db.query(models.Recipe).filter(models.Recipe.moderation_status == "ok")
    q = visibility.visible_authors(
        q, models.Recipe, visibility.hidden_author_ids(db, user)
    )

    rows = q.order_by(models.Recipe.created_at.desc()).limit(300).all()

    xp = user.xp_total or 0
    staff = visibility.is_staff(user)
    out = []
    for r in rows:
        rank = ranks.normalize_recipe_rank(r.rank, r.difficulty)
        if not staff and r.author_id != user.id and not ranks.can_access_recipe(xp, rank):
            continue
        out.append(
            {
                "id": r.id,
                "title": r.title,
                "origin": r.origin or "",
                "duration_min": r.duration_min or 0,
                "calories": r.calories or 0,
                "rank": rank,
            }
        )
        if len(out) >= CATALOGUE_LIMIT:
            break
    return out


def _conversation_or_404(db: Session, user: models.User, conversation_id: int):
    convo = (
        db.query(models.ChatConversation)
        .filter(
            models.ChatConversation.id == conversation_id,
            models.ChatConversation.user_id == user.id,
        )
        .first()
    )
    if not convo:
        raise HTTPException(404, "Conversația nu există")
    return convo


def _cards_for(db: Session, raw: str, user: models.User):
    """Rehidratează atașamentele unui mesaj. Rețetele se citesc din DB la
    fiecare afișare, ca una ștearsă între timp să dispară din fir în loc să
    rămână un card mort."""
    stored = {}
    if raw:
        try:
            stored = json.loads(raw) or {}
        except (ValueError, TypeError):
            stored = {}

    ids = stored.get("recipes") or []
    recipes = []
    if ids:
        rows = db.query(models.Recipe).filter(models.Recipe.id.in_(ids)).all()
        by_id = {r.id: r for r in rows}
        for rid in ids:
            r = by_id.get(rid)
            if r is not None and r.moderation_status == "ok":
                recipes.append(serializers.recipe_to_dict(db, r, viewer=user))
    return {"recipes": recipes, "nutrition": stored.get("nutrition")}


def _message_to_dict(db: Session, m: models.ChatMessage, user: models.User):
    cards = _cards_for(db, m.cards, user) if m.role == "ai" else {"recipes": [], "nutrition": None}
    return {
        "id": m.id,
        "role": m.role,
        "text": m.text or "",
        "has_photo": bool(m.has_photo),
        "recipes": cards["recipes"],
        "nutrition": cards["nutrition"],
        "created_at": serializers.iso_utc(m.created_at),
    }


def _convo_to_dict(c: models.ChatConversation):
    return {
        "id": c.id,
        "title": c.title or "New conversation",
        "created_at": serializers.iso_utc(c.created_at),
        "updated_at": serializers.iso_utc(c.updated_at),
    }


def _decode_image(data_uri: str) -> str:
    """Validează data-URI-ul primit de la frontend. Întoarce chiar data-URI-ul
    (asta primește Groq), dar numai după ce ne-am asigurat că e o imagine de
    dimensiune rezonabilă — altfel un payload uriaș ar bloca requestul."""
    if not data_uri:
        return ""
    if not data_uri.startswith("data:image/"):
        raise HTTPException(400, "Poza trebuie trimisă ca data-URI de imagine")
    try:
        b64 = data_uri.split(",", 1)[1]
        raw = base64.b64decode(b64, validate=False)
    except (IndexError, ValueError):
        raise HTTPException(400, "Poza nu a putut fi citită")
    if not raw:
        raise HTTPException(400, "Poză goală")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Imaginea depășește 8 MB")
    return data_uri


@router.get("/chat")
def list_conversations(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    limit: int = Query(30, le=100),
):
    convos = (
        db.query(models.ChatConversation)
        .filter(models.ChatConversation.user_id == user.id)
        .order_by(models.ChatConversation.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [_convo_to_dict(c) for c in convos]


@router.get("/chat/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    convo = _conversation_or_404(db, user, conversation_id)
    return {
        **_convo_to_dict(convo),
        "messages": [_message_to_dict(db, m, user) for m in convo.messages],
    }


@router.delete("/chat/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    convo = _conversation_or_404(db, user, conversation_id)
    db.delete(convo)
    db.commit()


@router.post("/chat")
def send_message(
    data: schemas.ChatAsk,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Un tur de conversație. Fără `conversation_id` se deschide un fir nou și
    modelul îi dă și un titlu, ca lista din bara laterală să fie utilă."""
    message = (data.message or "").strip()
    image = _decode_image(data.image or "")
    if not message and not image:
        raise HTTPException(400, "Scrie un mesaj sau trimite o poză")

    if data.conversation_id:
        convo = _conversation_or_404(db, user, data.conversation_id)
        is_new = False
    else:
        convo = models.ChatConversation(user_id=user.id, title="")
        db.add(convo)
        db.flush()
        is_new = True

    # Istoricul e ce s-a spus PÂNĂ acum; mesajul curent pleacă separat.
    history = [{"role": m.role, "text": m.text} for m in convo.messages]

    db.add(
        models.ChatMessage(
            conversation_id=convo.id,
            role="user",
            text=message,
            has_photo=bool(image),
        )
    )

    progress = ranks.progress_for_xp(user.xp_total or 0)
    answer = ai.chat_reply(
        message=message or "What do you see in this photo?",
        history=history,
        user_ctx={
            "name": user.full_name or user.username or "",
            "rank": progress.get("rank_name", ""),
        },
        catalogue=_accessible_recipes(db, user),
        image_data_uri=image or None,
        want_title=is_new,
    )

    cards = {"recipes": answer["recipe_ids"], "nutrition": answer["nutrition"]}
    ai_msg = models.ChatMessage(
        conversation_id=convo.id,
        role="ai",
        text=answer["text"],
        cards=json.dumps(cards, ensure_ascii=False),
    )
    db.add(ai_msg)

    if is_new:
        # Dacă modelul n-a dat titlu, cădem pe primele cuvinte ale întrebării —
        # tot e mai bun decât „New conversation" pe toate firele.
        fallback = (message or "Photo").strip()
        convo.title = answer["title"] or (fallback[:47] + "…" if len(fallback) > 48 else fallback)

    convo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ai_msg)

    return {
        "conversation": _convo_to_dict(convo),
        "message": _message_to_dict(db, ai_msg, user),
        "ok": answer["ok"],
    }
