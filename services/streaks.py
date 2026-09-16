# -*- coding: utf-8 -*-
"""Streak-urile — câte zile la rând ai ținut un obicei.

Patru la număr, trei simple și unul compus:

    lessons  o lecție terminată în ziua aia
    daily    o provocare zilnică revendicată
    cooking  o rețetă gătită și confirmată de AI (oricare, tu alegi)
    supreme  toate trei în aceeași zi

Ca și rank-ul, un streak NU se stochează: e o funcție pură de datele
evenimentelor pe care le avem deja. Un contor stocat trebuie decrementat de
cineva la miezul nopții — adică un scheduler, sau un cron care uită să ruleze,
sau un utilizator care își pierde streak-ul pentru că serverul a fost repornit.
Calculat din istoric, răspunsul e corect indiferent când e pusă întrebarea.

Ziua e UTC, la fel ca `daily_challenges.date` și `DailyDish.date`, ca să existe
o singură definiție a lui „azi" în tot backend-ul.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

import models

# Cele patru, în ordinea în care le arată interfața.
KINDS = ["lessons", "daily", "cooking", "supreme"]


def today() -> date:
    return datetime.utcnow().date()


def _days(values) -> set:
    """Datele (UTC) la care s-a întâmplat ceva, ignorând orele."""
    out = set()
    for value in values:
        if isinstance(value, datetime):
            out.add(value.date())
        elif isinstance(value, date):
            out.add(value)
    return out


def _longest(days: set) -> int:
    """Cea mai lungă serie de zile consecutive din tot istoricul."""
    best = 0
    for day in days:
        # numărăm doar din capătul de început al unei serii, ca să nu
        # re-parcurgem aceeași serie o dată pentru fiecare zi din ea
        if day - timedelta(days=1) in days:
            continue
        run = 1
        while day + timedelta(days=run) in days:
            run += 1
        best = max(best, run)
    return best


def _streak(days: set, now: date) -> dict:
    """Starea unui singur streak.

    Un streak e viu dacă ultima zi bifată e azi SAU ieri. Ieri contează pentru
    că altfel ziua ar începe cu streak-ul deja pierdut la 00:01, înainte să ai
    ocazia să faci ceva — ceea ce ar transforma obiceiul într-o pedeapsă.
    `at_risk` e exact starea aia: încă îl ai, dar îl pierzi la noapte.
    """
    done_today = now in days
    anchor = now if done_today else now - timedelta(days=1)
    current = 0
    if anchor in days:
        while anchor - timedelta(days=current) in days:
            current += 1
    return {
        "current": current,
        "longest": max(_longest(days), current),
        "total_days": len(days),
        "done_today": done_today,
        "alive": current > 0,
        "at_risk": current > 0 and not done_today,
        "last_day": max(days).isoformat() if days else None,
        # Ultimele 7 zile, cea mai veche prima, azi ultima. Un număr singur
        # spune „4" și atât; șirul ăsta arată și unde s-a rupt, ceea ce e
        # jumătate din motivul pentru care cineva se uită la un streak.
        "week": [(now - timedelta(days=offset)) in days for offset in range(6, -1, -1)],
    }


def _lesson_days(db: Session, user_id: int) -> set:
    rows = (
        db.query(models.LessonProgress.completed_at, models.LessonProgress.mastered_at)
        .filter(models.LessonProgress.user_id == user_id)
        .all()
    )
    # Mastery-ul e tot o lecție terminată în ziua aia — de multe ori într-o zi
    # diferită de quiz-ul de bază, deci amândouă datele contează.
    return _days([value for row in rows for value in row])


def _daily_days(db: Session, user_id: int) -> set:
    rows = (
        db.query(models.DailyChallengeDone.completed_at)
        .filter(models.DailyChallengeDone.user_id == user_id)
        .all()
    )
    return _days([row[0] for row in rows])


def _cooking_days(db: Session, user_id: int) -> set:
    rows = (
        db.query(models.CookLog.cooked_at)
        .filter(models.CookLog.user_id == user_id)
        .all()
    )
    return _days([row[0] for row in rows])


def for_user(db: Session, user) -> dict:
    """Toate patru, gata de trimis frontend-ului."""
    now = today()
    lessons = _lesson_days(db, user.id)
    daily = _daily_days(db, user.id)
    cooking = _cooking_days(db, user.id)
    # Supreme nu e „cel mai lung dintre celelalte trei": e ziua în care le-ai
    # făcut pe toate. Intersecția, nu maximul.
    supreme = lessons & daily & cooking

    return {
        "today": now.isoformat(),
        "lessons": _streak(lessons, now),
        "daily": _streak(daily, now),
        "cooking": _streak(cooking, now),
        "supreme": _streak(supreme, now),
    }
