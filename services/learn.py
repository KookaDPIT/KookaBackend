# -*- coding: utf-8 -*-
"""Logica arborelui Learn: seed, stări, corectarea quiz-urilor și XP.

Regulile centrale, într-un singur loc:

* O lecție e **available** dacă toate prerechizitele ei sunt terminate ȘI
  rank-ul userului a atins `req_tier`.
* Quiz-ul se corectează AICI, pe server. Răspunsurile corecte nu pleacă
  niciodată către browser (vezi `public_quiz`).
* Un quiz ratat pune lecția în cooldown 24h — în DB, nu în localStorage.
* **Mastery** cere trei lucruri: lecția terminată, quiz-ul avansat trecut și o
  rețetă gătită confirmată de AI *după* terminarea lecției.
"""
import json
import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

import models
from data import lessons_seed
from services import ranks

COOLDOWN_HOURS = 24
PASS_RATIO = 1.0          # quiz-ul cere 100% corect
MASTERY_TIER_GAP = 2      # quiz-ul avansat cere cu 2 trepte peste lecție


# ---------- XP ----------
def xp_for_tier(tier: int) -> int:
    """XP-ul unei lecții crește cu treapta cerută, ca o lecție de Platinum să
    conteze mai mult decât una de Copper. Calibrat astfel încât tot arborele
    (lecții + mastery) să ducă un utilizator aproape de Chef, dar nu peste."""
    return 120 + int(tier) * 22


def mastery_xp_for_tier(tier: int) -> int:
    return round(xp_for_tier(tier) * 0.5)


# ---------- seed ----------
# Așezarea: un fagure compact care crește din centru.
#
# Foundations ocupă hexagonul din mijloc, iar fiecare lecție se așază pe un
# hexagon LIPIT de lecția de care depinde — ca focul care se aprinde în mijloc
# și se întinde din aproape în aproape. Nu există spițe și nici secțiuni
# separate: toate cele 50 formează o singură masă continuă.
#
# Direcția ramurii rămâne, dar doar ca preferință slabă la alegerea celulei
# libere, cât să nu se încurce ramurile între ele. Compactitatea are prioritate,
# deci forma iese rotundă, nu în raze.
_SQRT3 = 3 ** 0.5


# Ponderi la alegerea celulei, în ordinea strictă a importanței:
#
#   1. lipirea de părinte — o lecție care nu atinge lecția din care decurge ar
#      rupe fagurele, deci costul unui pas în plus depășește orice altceva;
#   2. apropierea de centru — asta e ce ține forma rotundă și strânsă. Cu o
#      pondere mică, ramurile o luau drept în afară și ieșeau opt raze subțiri
#      cu goluri între ele; trebuie să depășească penalizarea maximă de unghi
#      (180 de grade), altfel direcția câștigă;
#   3. direcția ramurii — doar departajare, cât să nu se încurce ramurile.
_W_PARENT = 10000     # cât costă fiecare pas de depărtare față de părinte
_W_CENTRE = 300       # cât costă fiecare pas de depărtare față de centru
_W_ANGLE = 1.0        # cât costă abaterea (în grade) de la direcția ramurii

_SEARCH_RADIUS = 8    # cât de departe de centru căutăm celule libere


def hex_distance(a, b) -> int:
    """Distanța în pași de hexagon între două celule axiale."""
    dq, dr = a[0] - b[0], a[1] - b[1]
    return (abs(dq) + abs(dq + dr) + abs(dr)) // 2


def hex_to_pixel(q: int, r: int, size: float = 1.0):
    """Centrul hexagonului în pixeli (pointy-top), pentru unghiuri și distanțe."""
    return size * _SQRT3 * (q + r / 2), size * 1.5 * r


def _cells_within(radius: int):
    """Toate celulele aflate la cel mult `radius` pași de centru."""
    out = []
    for q in range(-radius, radius + 1):
        lo = max(-radius, -q - radius)
        hi = min(radius, -q + radius)
        for r in range(lo, hi + 1):
            out.append((q, r))
    return out


def _angle_gap(cell, angle_deg: float) -> float:
    """Cât de mult se abate direcția centru→celulă de la direcția ramurii, în
    grade (0..180). Celula centrală n-are direcție, deci nu penalizăm."""
    x, y = hex_to_pixel(*cell)
    if x == 0 and y == 0:
        return 0.0
    diff = abs(math.degrees(math.atan2(y, x)) - angle_deg) % 360
    return min(diff, 360 - diff)


def _place(parent, angle_deg: float, taken: set):
    """Cea mai bună celulă liberă pentru o lecție cu părintele dat.

    Preferăm, în ordinea ponderilor de mai sus: lipită de părinte, apoi cât mai
    aproape de centru, apoi pe direcția ramurii."""
    best, best_score = None, None
    for cell in _cells_within(_SEARCH_RADIUS):
        if cell in taken:
            continue
        score = (
            _W_PARENT * hex_distance(cell, parent)
            + _W_ANGLE * _angle_gap(cell, angle_deg)
            + _W_CENTRE * hex_distance(cell, (0, 0))
        )
        if best_score is None or score < best_score:
            best, best_score = cell, score
    return best


def _dump(value):
    return json.dumps(value, ensure_ascii=False)


def layout_plan() -> dict:
    """{slug: {depth, prereqs, q, r}} pentru toate cele 50 de noduri.

    Plasarea merge pe niveluri de adâncime, nu ramură cu ramură: dacă am umple
    o ramură până la capăt înainte de a începe următoarea, prima ar ocupa
    hexagoanele din apropierea centrului și le-ar împinge pe celelalte artificial
    în afară. Inel cu inel, toate cele opt ramuri cresc în același ritm, ca un
    foc aprins în mijloc."""
    angles = {b["id"]: b["angle"] for b in lessons_seed.BRANCHES}

    # pasul 1 — adâncimea și prerechizitele fiecărei lecții
    plan = {lessons_seed.ROOT["slug"]: {"depth": 0, "prereqs": [], "q": 0, "r": 0}}
    depth_by_branch = {}
    prev_by_branch = {}
    by_depth = {}
    for node in lessons_seed.LESSONS:
        branch = node["branch"]
        depth = depth_by_branch.get(branch, 0) + 1
        depth_by_branch[branch] = depth
        parent = prev_by_branch.get(branch, lessons_seed.ROOT["slug"])
        prev_by_branch[branch] = node["slug"]
        plan[node["slug"]] = {
            "depth": depth,
            "prereqs": [parent] + list(node.get("extra", [])),
        }
        by_depth.setdefault(depth, []).append((node["slug"], branch, parent))

    # pasul 2 — poziții: fiecare lecție se lipește de cea din care decurge
    taken = {(0, 0)}
    for depth in sorted(by_depth):
        for slug, branch, parent in by_depth[depth]:
            parent_pos = (plan[parent]["q"], plan[parent]["r"])
            q, r = _place(parent_pos, angles[branch], taken)
            taken.add((q, r))
            plan[slug]["q"] = q
            plan[slug]["r"] = r
    return plan


def seed_lessons(db: Session) -> int:
    """Scrie/actualizează cele 50 de lecții din fișierele de seed.

    Rulează la fiecare pornire ca să propage schimbările de conținut, dar
    NU atinge lecțiile marcate `custom` — acelea au fost editate din /admin și
    editarea manuală trebuie să câștige."""
    written = 0
    plan = layout_plan()

    for node in lessons_seed.ALL_NODES:
        branch = node.get("branch", "root")
        spot = plan[node["slug"]]
        depth, prereqs = spot["depth"], spot["prereqs"]
        q, r = spot["q"], spot["r"]
        tier = int(node["req_tier"])

        row = db.query(models.Lesson).filter(models.Lesson.slug == node["slug"]).first()
        if row is None:
            row = models.Lesson(slug=node["slug"])
            db.add(row)
        elif row.custom:
            continue

        row.title = node["title"]
        row.branch = branch
        row.icon = node["icon"]
        row.summary = node["summary"]
        row.content = node["intro"]
        row.steps = _dump(node["steps"])
        row.tips = _dump(node["tips"])
        row.quiz = _dump(node["quiz"])
        row.mastery_quiz = _dump(node["mastery_quiz"])
        row.prereqs = _dump(prereqs)
        row.req_tier = tier
        row.est_min = int(node["est_min"])
        row.xp = xp_for_tier(tier)
        row.mastery_xp = mastery_xp_for_tier(tier)
        row.hex_q, row.hex_r = q, r
        row.depth = depth
        row.order = depth
        written += 1

    db.commit()
    return written


# ---------- citire ----------
def _load(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def public_quiz(raw) -> list:
    """Quiz-ul fără indexul răspunsului corect — forma trimisă spre browser."""
    return [
        {"q": item.get("q", ""), "options": list(item.get("options", []))}
        for item in _load(raw, [])
    ]


def _progress_map(db: Session, user_id: int) -> dict:
    rows = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user_id)
        .all()
    )
    return {row.lesson_id: row for row in rows}


def _future(dt) -> bool:
    return bool(dt and dt > datetime.utcnow())


def node_state(lesson, progress, completed_slugs: set, tier: int) -> tuple:
    """(state, lock_reason). state ∈ locked | available | completed | mastered."""
    if progress is not None and progress.mastered:
        return "mastered", None
    if progress is not None and progress.completed:
        return "completed", None

    prereqs = _load(lesson.prereqs, [])
    prereqs_done = all(slug in completed_slugs for slug in prereqs)
    rank_ok = tier >= (lesson.req_tier or 0)

    if prereqs_done and rank_ok:
        return "available", None
    if not prereqs_done:
        return "locked", "prereq"
    return "locked", "rank"


def _verified_cook_after(db: Session, user_id: int, since) -> bool:
    """A gătit userul ceva confirmat de AI după momentul dat? Condiția practică
    pentru mastery."""
    q = (
        db.query(models.SavedRecipe)
        .filter(
            models.SavedRecipe.user_id == user_id,
            models.SavedRecipe.cooked_verified.is_(True),
        )
    )
    if since is not None:
        q = q.filter(models.SavedRecipe.cooked_at.isnot(None),
                     models.SavedRecipe.cooked_at >= since)
    return q.first() is not None


def lesson_card(lesson, state, lock_reason, progress) -> dict:
    """Forma scurtă, pentru fagure."""
    return {
        "slug": lesson.slug,
        "title": lesson.title,
        "branch": lesson.branch,
        "icon": lesson.icon or "",
        "summary": lesson.summary or "",
        "req_tier": lesson.req_tier or 0,
        "req_tier_label": ranks.tier_label(lesson.req_tier or 0),
        "est_min": lesson.est_min or 0,
        "xp": lesson.xp or 0,
        "mastery_xp": lesson.mastery_xp or 0,
        "prereqs": _load(lesson.prereqs, []),
        "q": lesson.hex_q or 0,
        "r": lesson.hex_r or 0,
        "depth": lesson.depth or 0,
        "state": state,
        "lock_reason": lock_reason,
        "mastery_passed": bool(progress and progress.mastery_passed),
        "cooldown_until": progress.cooldown_until.isoformat() + "Z"
        if progress and _future(progress.cooldown_until) else None,
    }


def build_tree(db: Session, user) -> dict:
    """Tot ce-i trebuie paginii Learn ca să deseneze fagurele."""
    lessons = db.query(models.Lesson).order_by(models.Lesson.id).all()
    progress = _progress_map(db, user.id)
    tier = ranks.tier_for_xp(user.xp_total)

    completed_slugs = {
        lesson.slug for lesson in lessons
        if (p := progress.get(lesson.id)) is not None and p.completed
    }

    nodes = []
    for lesson in lessons:
        p = progress.get(lesson.id)
        state, reason = node_state(lesson, p, completed_slugs, tier)
        nodes.append(lesson_card(lesson, state, reason, p))

    done = sum(1 for n in nodes if n["state"] in ("completed", "mastered"))
    mastered = sum(1 for n in nodes if n["state"] == "mastered")

    return {
        "rank": ranks.progress_for_xp(user.xp_total),
        "ranks": ranks.table(),
        "branches": lessons_seed.BRANCHES,
        "lessons": nodes,
        "stats": {
            "total": len(nodes),
            "completed": done,
            "mastered": mastered,
            "available": sum(1 for n in nodes if n["state"] == "available"),
        },
    }


def lesson_detail(db: Session, user, lesson) -> dict:
    """Detaliul unei lecții — conținut complet, quiz fără răspunsuri."""
    lessons = db.query(models.Lesson).all()
    progress = _progress_map(db, user.id)
    tier = ranks.tier_for_xp(user.xp_total)
    completed_slugs = {
        l.slug for l in lessons
        if (p := progress.get(l.id)) is not None and p.completed
    }
    p = progress.get(lesson.id)
    state, reason = node_state(lesson, p, completed_slugs, tier)

    mastery_tier = min(ranks.MAX_TIER, (lesson.req_tier or 0) + MASTERY_TIER_GAP)
    completed_at = p.completed_at if p else None
    cooked = _verified_cook_after(db, user.id, completed_at) if (p and p.completed) else False

    data = lesson_card(lesson, state, reason, p)
    data.update({
        "intro": lesson.content or "",
        "steps": _load(lesson.steps, []),
        "tips": _load(lesson.tips, []),
        "video_url": lesson.video_url or "",
        "quiz": public_quiz(lesson.quiz),
        "attempts": p.attempts if p else 0,
        "unlocks": [
            l.title for l in lessons
            if lesson.slug in _load(l.prereqs, [])
        ],
        "mastery": {
            "req_tier": mastery_tier,
            "req_tier_label": ranks.tier_label(mastery_tier),
            "rank_ok": tier >= mastery_tier,
            "quiz_passed": bool(p and p.mastery_passed),
            "cook_done": cooked,
            "mastered": bool(p and p.mastered),
            "xp": lesson.mastery_xp or 0,
            "quiz": public_quiz(lesson.mastery_quiz),
            "cooldown_until": p.mastery_cooldown_until.isoformat() + "Z"
            if p and _future(p.mastery_cooldown_until) else None,
        },
    })
    return data


# ---------- scriere ----------
def award_xp(user, amount: int) -> dict:
    """Adaugă XP și raportează dacă s-a schimbat treapta de rank."""
    before = ranks.tier_for_xp(user.xp_total)
    user.xp_total = max(0, int(user.xp_total or 0)) + int(amount)
    after = ranks.tier_for_xp(user.xp_total)
    # `level` e păstrat doar ca oglindă pentru consumatorii vechi ai API-ului;
    # rank-ul e sursa adevărului și se calculează din xp_total.
    user.level = after + 1
    return {
        "xp_gained": int(amount),
        "rank_up": after > before,
        "rank": ranks.progress_for_xp(user.xp_total),
    }


def get_or_create_progress(db: Session, user_id: int, lesson_id: int):
    row = (
        db.query(models.LessonProgress)
        .filter(
            models.LessonProgress.user_id == user_id,
            models.LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )
    if row is None:
        row = models.LessonProgress(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
        db.flush()
    return row


def score_answers(raw_quiz, answers: list) -> tuple:
    """(corecte, total). Un răspuns lipsă sau în afara intervalului e greșit."""
    questions = _load(raw_quiz, [])
    total = len(questions)
    correct = 0
    for i, question in enumerate(questions):
        given = answers[i] if i < len(answers) else None
        if given is not None and given == question.get("correct"):
            correct += 1
    return correct, total


def cooldown_from_now():
    return datetime.utcnow() + timedelta(hours=COOLDOWN_HOURS)
