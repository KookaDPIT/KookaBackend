"""Cine are voie să vadă conținutul cui.

Un singur loc pentru regula „acest cont e ascuns", ca să nu ajungă implementată
de cinci ori ușor diferit prin routere. Un cont e ascuns când:

  * e suspendat (`suspended_until` în viitor) — sancțiune temporară;
  * e dezactivat (`is_active` fals) — sancțiune fără termen;
  * e blocat de cel care se uită, sau l-a blocat pe el (blocarea taie vizibilitatea
    în ambele sensuri, altfel blochezi pe cineva și îi vezi în continuare postările).

Ascuns înseamnă complet: rețetele, postările de forum și profilul dispar din
listări, din căutare ȘI de la accesul direct pe URL (404, nu 403 — un 403 ar
confirma că acel cont există). Excepții deliberate:

  * moderatorii și adminii văd tot, altfel n-ar avea ce modera;
  * fiecare își vede propriul conținut, ca un cont suspendat să înțeleagă ce se
    întâmplă când se autentifică, în loc să găsească un profil gol.
"""
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from deps import ROLE_LEVELS


def is_staff(user) -> bool:
    return user is not None and ROLE_LEVELS.get(user.role, 0) >= ROLE_LEVELS["moderator"]


def is_suspended(user) -> bool:
    if user is None:
        return False
    return bool(user.suspended_until and user.suspended_until > datetime.utcnow())


def is_silenced(user) -> bool:
    """Suspendat sau dezactivat — în ambele cazuri conținutul nu se mai vede."""
    return is_suspended(user) or not bool(user.is_active)


def silenced_user_ids(db: Session) -> set:
    """Toate conturile suspendate sau dezactivate."""
    now = datetime.utcnow()
    rows = (
        db.query(models.User.id)
        .filter(
            or_(
                models.User.is_active == False,  # noqa: E712 — SQL, nu Python
                models.User.suspended_until > now,
            )
        )
        .all()
    )
    return {r[0] for r in rows}


def blocked_user_ids(db: Session, viewer) -> set:
    """Conturile dintre care și cel care se uită există o blocare, în orice sens."""
    if viewer is None:
        return set()
    rows = (
        db.query(models.Block.blocker_id, models.Block.blocked_id)
        .filter(
            or_(
                models.Block.blocker_id == viewer.id,
                models.Block.blocked_id == viewer.id,
            )
        )
        .all()
    )
    out = set()
    for blocker, blocked in rows:
        out.add(blocked if blocker == viewer.id else blocker)
    return out


def hidden_author_ids(db: Session, viewer=None) -> set:
    """Autorii al căror conținut nu trebuie să ajungă la `viewer`."""
    if is_staff(viewer):
        return set()
    hidden = silenced_user_ids(db) | blocked_user_ids(db, viewer)
    if viewer is not None:
        hidden.discard(viewer.id)  # propriul conținut rămâne vizibil posesorului
    return hidden


def visible_authors(query, model, hidden_ids):
    """Adaugă filtrul de autor pe un query, dacă e ceva de ascuns."""
    if not hidden_ids:
        return query
    return query.filter(
        or_(model.author_id.is_(None), model.author_id.notin_(hidden_ids))
    )


def can_see_user(db: Session, target, viewer) -> bool:
    """Profilul acestui cont poate fi deschis de `viewer`?"""
    if target is None:
        return False
    if is_staff(viewer):
        return True
    if viewer is not None and viewer.id == target.id:
        return True
    return target.id not in hidden_author_ids(db, viewer)
