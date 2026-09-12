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
import unicodedata
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from database import get_db
from deps import get_current_user
from services import ai, planner, ranks, visibility

router = APIRouter(prefix="/ai", tags=["ai"])

# O poză trimisă în chat: ajunge la model ca data-URI efemer și NU se stochează.
MAX_IMAGE_BYTES = 8 * 1024 * 1024
# Câte rețete îi arătăm modelului ca să aibă din ce alege. Ține-l mic: fiecare
# linie se plătește în tokeni la FIECARE mesaj, iar modelul oricum recomandă cel
# mult trei. Cele trimise sunt cele mai apropiate de întrebare (vezi
# `_rank_catalogue`), completate cu cele mai noi.
CATALOGUE_LIMIT = 15
# Din câte rețete alegem cele CATALOGUE_LIMIT. Filtrarea se face în Python, nu
# în SQL, ca să meargă la fel pe Postgres și pe SQLite.
CATALOGUE_POOL = 300
# Cât de mult trebuie să semene două titluri ca să le tratăm drept același
# preparat. 0.5 prinde „Carbonara" / „Spaghetti carbonara" fără să lipească
# „Tomato soup" de „Tomato pasta".
TITLE_SIMILARITY = 0.5

# Cuvinte care apar în orice întrebare și n-ar face decât să potrivească la
# întâmplare („what can I make with...").
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "but", "can", "cook",
    "cooking", "could", "do", "does", "eat", "find", "food", "for", "from", "get",
    "give", "good", "got", "has", "have", "how", "i", "if", "in", "is", "it",
    "its", "just", "know", "like", "make", "me", "my", "need", "not", "of", "on",
    "or", "recipe", "recipes", "should", "so", "some", "something", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "to", "up", "use",
    "want", "was", "what", "when", "where", "which", "who", "will", "with",
    "would", "you", "your",
}


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

def _batch_stats(db: Session, ids: list):
    """(avg_rating, review_count, saves) pentru multe rețete deodată.

    `serializers.recipe_stats` face trei interogări per rețetă — pe 300 de
    rețete ar însemna sute de query-uri la fiecare mesaj din chat. Aici sunt
    două, indiferent câte rețete avem.
    """
    if not ids:
        return {}
    stats = {rid: {"avg": 0.0, "reviews": 0, "saves": 0} for rid in ids}

    rows = (
        db.query(
            models.Review.recipe_id,
            func.avg(models.Review.rating),
            func.count(models.Review.id),
        )
        .filter(models.Review.recipe_id.in_(ids))
        .group_by(models.Review.recipe_id)
        .all()
    )
    for rid, avg, count in rows:
        stats[rid]["avg"] = float(avg or 0)
        stats[rid]["reviews"] = int(count or 0)

    rows = (
        db.query(models.SavedRecipe.recipe_id, func.count(models.SavedRecipe.id))
        .filter(models.SavedRecipe.recipe_id.in_(ids))
        .group_by(models.SavedRecipe.recipe_id)
        .all()
    )
    for rid, count in rows:
        stats[rid]["saves"] = int(count or 0)

    return stats


def _title_tokens(title: str):
    """Titlul redus la esență, pentru comparat: fără diacritice, fără
    punctuație, fără glosarul din paranteză și fără cuvinte de umplutură.
    „Ouă ochiuri cu roșii (sunny-side-up eggs)" și „Oua ochiuri cu rosii" ajung
    la același set."""
    text = title or ""
    # glosa dintre paranteze e traducere, nu preparat diferit
    while "(" in text and ")" in text:
        start, end = text.index("("), text.index(")")
        if start > end:
            break
        text = text[:start] + " " + text[end + 1:]
    flat = unicodedata.normalize("NFKD", text)
    flat = "".join(c for c in flat if not unicodedata.combining(c))
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in flat)
    return {w for w in cleaned.split() if len(w) > 2 and w not in _STOPWORDS}


def _similar(a: set, b: set) -> bool:
    """Două titluri despre același preparat.

    Doar Jaccard nu e destul: „Carbonara" și „Spaghetti carbonara" ies la 0.5
    și ar rămâne separate, deși sunt evident aceeași rețetă. Așa că cerem două
    lucruri deodată — titlul scurt să fie aproape complet cuprins în celălalt
    (containment), dar cele două să nu difere prea mult ca lungime (Jaccard).
    A doua condiție e cea care ține „Carbonara" departe de „Carbonara with peas
    and bacon", care chiar e alt preparat.
    """
    if not a or not b:
        return False
    common = len(a & b)
    if not common:
        return False
    containment = common / min(len(a), len(b))
    jaccard = common / len(a | b)
    return containment >= 0.8 and jaccard >= TITLE_SIMILARITY


def _quality_score(r: dict) -> float:
    """Cât de bună e o rețetă, când trebuie să alegem una dintre mai multe
    variante ale aceluiași preparat.

    Nota se trage spre medie când sunt puține recenzii (un singur 5 nu trebuie
    să bată un 4.6 din patruzeci), apoi contează cât de completă e rețeta —
    una cu poză și cu nutriție calculată e mai utilă cuiva care o deschide.
    """
    prior, weight = 3.5, 5.0        # media presupusă și cât de repede o părăsim
    reviews = r.get("reviews", 0)
    rating = ((r.get("avg", 0.0) * reviews) + (prior * weight)) / (reviews + weight)

    score = rating * 10
    score += min(r.get("saves", 0), 20) * 0.5
    score += min(reviews, 20) * 0.2
    if r.get("has_image"):
        score += 3
    if r.get("calories"):
        score += 1
    if r.get("has_description"):
        score += 1
    return score


def _dedupe_by_dish(rows: list):
    """Un singur card per preparat: cea mai bună variantă a fiecăruia.

    Fără asta, un chat care recomandă „ouă ochiuri" arată trei carduri aproape
    identice, pentru că trei utilizatori au publicat aceeași rețetă.
    """
    groups = []                      # [(tokens, [rows...])]
    for r in rows:
        tokens = _title_tokens(r["title"])
        for group_tokens, members in groups:
            if _similar(tokens, group_tokens):
                members.append(r)
                break
        else:
            groups.append((tokens, [r]))

    out = []
    for _, members in groups:
        best = max(members, key=_quality_score)
        # spunem modelului câte variante am strâns, ca să nu pretindă că e unica
        best = dict(best, duplicates=len(members) - 1)
        out.append(best)
    return out


def _keywords(text: str):
    """Cuvintele purtătoare de sens dintr-o întrebare, pentru potrivire."""
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or ""))
    return {w for w in cleaned.split() if len(w) > 2 and w not in _STOPWORDS}


def _same_stem(a: str, b: str, n: int = 4) -> bool:
    """Potrivire slabă pe rădăcină: „italian"/„Italy", „tomatoes"/„tomato".
    Fără librărie de stemming — n-avem nevoie de mai mult decât atât aici."""
    return len(a) >= n and len(b) >= n and a[:n] == b[:n]


def _rank_catalogue(rows: list, message: str, limit: int = CATALOGUE_LIMIT):
    """Cele mai potrivite `limit` rețete pentru întrebare.

    Punctajul e simplu — câte cuvinte din întrebare apar în titlu sau în țara de
    origine. Nu e căutare semantică și nici nu trebuie să fie: rolul ei e doar
    să ridice deasupra rețetele plauzibile. Lista se completează întotdeauna
    până la `limit` cu cele mai noi, ca modelul să aibă ce recomanda și când
    întrebarea nu seamănă cu nimic („ceva de cină?").
    """
    words = _keywords(message)
    if words:
        scored = []
        for r in rows:
            tokens = _keywords(f"{r['title']} {r.get('origin', '')}")
            haystack = f"{r['title']} {r.get('origin', '')}".lower()
            score = 0
            for w in words:
                if w in haystack:
                    score += 2                      # potrivire directă: „chicken"
                elif any(_same_stem(w, t) for t in tokens):
                    score += 1                      # „italian" ~ „Italy"
            if score:
                scored.append((score, r))
        scored.sort(key=lambda pair: -pair[0])
        out = [r for _, r in scored[:limit]]
    else:
        out = []

    if len(out) < limit:
        seen = {r["id"] for r in out}
        for r in rows:                      # `rows` vine deja de la nou la vechi
            if r["id"] not in seen:
                out.append(r)
                if len(out) >= limit:
                    break
    return out


def _accessible_recipes(db: Session, user: models.User, message: str = ""):
    """Rețetele pe care userul chiar le poate deschide, restrânse la cele
    relevante pentru întrebare. Aceleași filtre ca la listare, plus poarta de
    rank — n-are rost să-i recomandăm ceva ce se lovește de un 403 la click."""
    q = db.query(models.Recipe).filter(models.Recipe.moderation_status == "ok")
    q = visibility.visible_authors(
        q, models.Recipe, visibility.hidden_author_ids(db, user)
    )

    rows = q.order_by(models.Recipe.created_at.desc()).limit(CATALOGUE_POOL).all()

    xp = user.xp_total or 0
    staff = visibility.is_staff(user)
    visible = [
        r for r in rows
        if staff
        or r.author_id == user.id
        or ranks.can_access_recipe(
            xp, ranks.normalize_recipe_rank(r.rank, r.difficulty)
        )
    ]

    stats = _batch_stats(db, [r.id for r in visible])
    allowed = []
    for r in visible:
        st = stats.get(r.id, {})
        allowed.append(
            {
                "id": r.id,
                "title": r.title,
                "origin": r.origin or "",
                "duration_min": r.duration_min or 0,
                "calories": r.calories or 0,
                "rank": ranks.normalize_recipe_rank(r.rank, r.difficulty),
                "avg": st.get("avg", 0.0),
                "reviews": st.get("reviews", 0),
                "saves": st.get("saves", 0),
                "has_image": bool(r.image_url),
                "has_description": bool(r.description),
            }
        )

    # Întâi scăpăm de variantele duplicate ale aceluiași preparat, apoi alegem
    # cele mai potrivite pentru întrebare — altfel cele 15 locuri s-ar umple cu
    # aceeași rețetă publicată de trei oameni.
    return _rank_catalogue(_dedupe_by_dish(allowed), message)


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
    return {
        "recipes": recipes,
        "nutrition": stored.get("nutrition"),
        # A record of what was done, not a live view: the card says what this
        # turn added, even if the person has since ticked it off the list.
        "plan": stored.get("plan"),
    }


def _plan_card(db: Session, applied: dict):
    """Ce a scris asistentul de fapt — nu ce a cerut.

    Modelul poate cere douăzeci de linii; card-ul arată doar rândurile care au
    intrat în DB, ca omul să vadă exact ce s-a schimbat."""
    if not applied or (not applied.get("shopping") and not applied.get("meals")):
        return None
    return {
        "shopping": [
            {
                "name": i.name,
                "quantity": i.quantity or "",
                "unit": i.unit or "",
            }
            for i in applied.get("shopping", [])
        ],
        "meals": [
            {
                "date": m.date,
                "slot": m.slot,
                "title": m.title,
                "recipe_id": m.recipe_id,
            }
            for m in applied.get("meals", [])
        ],
    }


def _message_to_dict(db: Session, m: models.ChatMessage, user: models.User):
    cards = (
        _cards_for(db, m.cards, user)
        if m.role == "ai"
        else {"recipes": [], "nutrition": None, "plan": None}
    )
    return {
        "id": m.id,
        "role": m.role,
        "text": m.text or "",
        "has_photo": bool(m.has_photo),
        "recipes": cards["recipes"],
        "nutrition": cards["nutrition"],
        "plan": cards.get("plan"),
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
        catalogue=_accessible_recipes(db, user, message),
        image_data_uri=image or None,
        want_title=is_new,
        # what is already on their list and in their calendar, so "add what I
        # need" does not duplicate half of it
        planner_lines=planner.summarize_for_model(db, user),
    )

    # The assistant can write to the shopping list and the meal plan. Every
    # field is re-validated inside services/planner.py, which is the same code
    # the buttons on the planner page go through — so a hallucinated recipe id
    # or an impossible date turns into a plain title or today, never a bad row.
    applied = planner.apply_ai_plan(db, user, answer.get("plan"))
    plan_card = _plan_card(db, applied)

    cards = {
        "recipes": answer["recipe_ids"],
        "nutrition": answer["nutrition"],
        "plan": plan_card,
    }
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
