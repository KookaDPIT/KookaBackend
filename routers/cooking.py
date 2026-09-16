"""Sesiunile de gătit — cum a decurs o gătire, nu doar dacă s-a terminat.

Pagina de cook-along raportează aici. Tot ce se strânge alimentează trofeele
(services/trophies.py): durată, cereri de ajutor, cronometre sărite, ieșiri din
aplicație, abandonuri.

Toate scrierile sunt tolerante: un eveniment pierdut înseamnă un trofeu ratat,
nu o gătire stricată, deci nimic de aici nu poate bloca bucătarul.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/cook", tags=["cooking"])


class SessionStart(BaseModel):
    recipe_id: int
    steps_total: int = 0
    timers_available: int = 0


class SessionEvent(BaseModel):
    """Un lot de incremente. Frontend-ul trimite doar ce s-a schimbat.

    Incremente, nu valori absolute: două file deschise pe aceeași rețetă ar
    scrie una peste alta dacă ar trimite totaluri.
    """
    ai_asks: int = 0
    ai_step: int | None = None     # indexul pasului la care s-a cerut ajutor
    timer_started: bool = False
    left_app: bool = False
    gave_up: bool = False


def _owned(db: Session, session_id: int, user_id: int) -> models.CookSession:
    row = (
        db.query(models.CookSession)
        .filter(
            models.CookSession.id == session_id,
            models.CookSession.user_id == user_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(404, "Sesiunea nu există")
    return row


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def start_session(
    data: SessionStart,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Deschide o sesiune. Una nouă la fiecare intrare în cook-along.

    Nu reutilizăm o sesiune deschisă pentru aceeași rețetă: a începe din nou
    după ce ai lăsat baltă e o a doua încercare, iar „te-ai întors și ai
    terminat" e tocmai ce măsoară „Comeback Kid".
    """
    recipe = db.query(models.Recipe).filter(models.Recipe.id == data.recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")

    row = models.CookSession(
        user_id=user.id,
        recipe_id=data.recipe_id,
        steps_total=max(0, data.steps_total),
        timers_available=max(0, data.timers_available),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.patch("/sessions/{session_id}")
def update_session(
    session_id: int,
    data: SessionEvent,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    row = _owned(db, session_id, user.id)

    if data.ai_asks:
        row.ai_asks = (row.ai_asks or 0) + data.ai_asks
        if (row.first_ask_after or -1) < 0:
            row.first_ask_after = max(
                0, int((datetime.utcnow() - row.started_at).total_seconds())
            )
    # `ai_steps` numără pași distincți, iar frontend-ul știe care sunt deja
    # marcați — trimite indexul doar prima dată pentru fiecare pas.
    if data.ai_step is not None:
        row.ai_steps = (row.ai_steps or 0) + 1
    if data.timer_started:
        row.timers_started = (row.timers_started or 0) + 1
    if data.left_app:
        row.left_app = True
    if data.gave_up and row.gave_up_at is None:
        row.gave_up_at = datetime.utcnow()

    db.commit()
    return {"ok": True}
