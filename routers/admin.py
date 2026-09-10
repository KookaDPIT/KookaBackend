"""Moderare: rețete flagged, ștergere/ascundere rețetă, și uneltele de roluri
(listare utilizatori, schimbare rol, suspendare, activare/dezactivare)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from serializers import iso_utc
from database import get_db
from deps import ROLE_LEVELS, get_current_admin, require_role
from services import visibility

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/recipes")
def list_for_moderation(
    status_filter: str = Query("flagged", alias="status"),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipes = (
        db.query(models.Recipe)
        .filter(models.Recipe.moderation_status == status_filter)
        .order_by(models.Recipe.created_at.desc())
        .all()
    )
    return [serializers.recipe_to_dict(db, r, full=True) for r in recipes]


def purge_recipe(db: Session, recipe: models.Recipe):
    """Șterge rețeta ȘI tot ce trimite la ea. Fără asta rămân recenzii și
    salvări orfane, iar rețeta continuă să apară în activitatea și în pașaportul
    conturilor care o gătiseră — o fantomă pe care nimeni n-o mai poate deschide."""
    db.query(models.Review).filter(models.Review.recipe_id == recipe.id).delete()
    db.query(models.SavedRecipe).filter(models.SavedRecipe.recipe_id == recipe.id).delete()
    db.query(models.DailyDish).filter(models.DailyDish.recipe_id == recipe.id).delete()
    db.delete(recipe)
    db.commit()


@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    purge_recipe(db, recipe)
    return {"deleted": True}


@router.post("/recipes/{recipe_id}/hide")
def hide_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    recipe.moderation_status = "hidden"
    db.commit()
    return {"hidden": True}


@router.post("/recipes/{recipe_id}/restore")
def restore_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Repune o rețetă ascunsă înapoi în circulație."""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Rețeta nu există")
    recipe.moderation_status = "ok"
    db.commit()
    return {"restored": True}


# ==========================================================================
#  MODERAREA FORUMULUI — aceleași unelte ca la rețete
# ==========================================================================

@router.get("/forum/posts")
def list_forum_for_moderation(
    status_filter: str = Query("ok", alias="status"),
    q: str = Query(""),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    query = db.query(models.ForumPost).filter(
        models.ForumPost.moderation_status == status_filter
    )
    term = q.strip()
    if term:
        if term.lstrip("#").isdigit():
            query = query.filter(models.ForumPost.id == int(term.lstrip("#")))
        else:
            query = query.filter(func.lower(models.ForumPost.title).like(f"%{term.lower()}%"))

    posts = query.order_by(models.ForumPost.created_at.desc()).limit(100).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "excerpt": (p.body or "")[:160],
            "language": p.language or "en",
            "tag": p.tag or "question",
            "votes": p.votes or 0,
            "moderation_status": p.moderation_status or "ok",
            "author": serializers.author_mini(p.author),
            "created_at": iso_utc(p.created_at),
        }
        for p in posts
    ]


@router.post("/forum/posts/{post_id}/hide")
def hide_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    post.moderation_status = "hidden"
    db.commit()
    return {"hidden": True}


@router.post("/forum/posts/{post_id}/restore")
def restore_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    post.moderation_status = "ok"
    db.commit()
    return {"restored": True}


@router.delete("/forum/posts/{post_id}")
def delete_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    db.query(models.ForumComment).filter(models.ForumComment.post_id == post_id).delete()
    db.query(models.ForumVote).filter(models.ForumVote.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return {"deleted": True}


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.role == "admin":
        raise HTTPException(403, "Nu poți dezactiva un admin")
    u.is_active = False
    db.commit()
    return {"deactivated": True}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    u.is_active = True
    db.commit()
    return {"activated": True}


# ==========================================================================
#  UNELTELE DE ROLURI
#  Listarea și suspendarea sunt pentru moderatori; schimbarea rolului doar
#  pentru admini (require_role("admin")), ca un moderator să nu se poată
#  auto-promova.
# ==========================================================================

def _admin_user_dict(u: models.User):
    """Vedere de moderare a unui cont: include câmpurile pe care serializatorul
    public le ascunde (email, rol, stare, suspendare)."""
    suspended = bool(u.suspended_until and u.suspended_until > datetime.utcnow())
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name or "",
        "email": u.email,
        "avatar_url": u.avatar_url or "",
        "role": u.role or "user",
        "is_active": bool(u.is_active),
        "suspended": suspended,
        "suspended_until": iso_utc(u.suspended_until),
        "level": u.level,
        "created_at": iso_utc(u.created_at),
    }


@router.get("/users")
def list_users(
    q: str = Query("", description="caută după username, nume sau email"),
    role: str = Query("", description="filtrează după rol"),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    query = db.query(models.User)

    term = q.strip().lower()
    if term:
        like = f"%{term}%"
        query = query.filter(
            or_(
                func.lower(models.User.username).like(like),
                func.lower(models.User.full_name).like(like),
                func.lower(models.User.email).like(like),
            )
        )
    if role.strip():
        query = query.filter(models.User.role == role.strip())

    rows = query.order_by(models.User.created_at.desc()).limit(100).all()
    return [_admin_user_dict(u) for u in rows]


@router.patch("/users/{user_id}/role")
def set_role(
    user_id: int,
    data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    role = data.role.strip().lower()
    if role not in ROLE_LEVELS:
        raise HTTPException(400, f"Rol invalid. Alege dintre: {', '.join(ROLE_LEVELS)}")

    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.id == admin.id:
        raise HTTPException(400, "Nu-ți poți schimba propriul rol")

    u.role = role
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    data: schemas.SuspendRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Suspendare temporară: contul rămâne activ (poate citi), dar rutele care
    folosesc deps.require_not_suspended îi refuză scrierea până la termen."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    if u.id == admin.id:
        raise HTTPException(400, "Nu te poți suspenda pe tine")
    if ROLE_LEVELS.get(u.role, 0) >= ROLE_LEVELS.get(admin.role, 0):
        raise HTTPException(403, "Nu poți suspenda un cont cu rol egal sau superior")

    u.suspended_until = datetime.utcnow() + timedelta(hours=data.hours or (data.days * 24))
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)


@router.delete("/users/{user_id}/suspend")
def unsuspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Utilizatorul nu există")
    u.suspended_until = None
    db.commit()
    db.refresh(u)
    return _admin_user_dict(u)


# ---------- LECȚII (Learn) ----------
# Editarea unei lecții o marchează `custom`, așa că seed-ul de la pornire n-o
# mai rescrie. `POST /admin/lessons/{slug}/reset` renunță la editare și readuce
# lecția la conținutul din fișierele de seed.

def _lesson_admin_dict(db: Session, lesson: models.Lesson):
    from services import learn as learn_service, ranks as ranks_service

    finished = (
        db.query(func.count(models.LessonProgress.id))
        .filter(
            models.LessonProgress.lesson_id == lesson.id,
            models.LessonProgress.completed.is_(True),
        )
        .scalar()
    )
    mastered = (
        db.query(func.count(models.LessonProgress.id))
        .filter(
            models.LessonProgress.lesson_id == lesson.id,
            models.LessonProgress.mastered.is_(True),
        )
        .scalar()
    )
    return {
        "slug": lesson.slug,
        "title": lesson.title,
        "branch": lesson.branch,
        "icon": lesson.icon or "",
        "summary": lesson.summary or "",
        "intro": lesson.content or "",
        "video_url": lesson.video_url or "",
        "req_tier": lesson.req_tier or 0,
        "req_tier_label": ranks_service.tier_label(lesson.req_tier or 0),
        "est_min": lesson.est_min or 0,
        "xp": lesson.xp or 0,
        "mastery_xp": lesson.mastery_xp or 0,
        "depth": lesson.depth or 0,
        "custom": bool(lesson.custom),
        "steps": learn_service._load(lesson.steps, []),
        "tips": learn_service._load(lesson.tips, []),
        "prereqs": learn_service._load(lesson.prereqs, []),
        # Aici răspunsurile corecte SUNT incluse: e o consolă de administrare,
        # protejată de require_role("admin"), unde editarea lor e scopul.
        "quiz": learn_service._load(lesson.quiz, []),
        "mastery_quiz": learn_service._load(lesson.mastery_quiz, []),
        "stats": {"completed": int(finished or 0), "mastered": int(mastered or 0)},
    }


@router.get("/lessons")
def list_lessons(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    lessons = db.query(models.Lesson).order_by(
        models.Lesson.branch, models.Lesson.depth
    ).all()
    return [_lesson_admin_dict(db, lesson) for lesson in lessons]


@router.get("/lessons/{slug}")
def get_lesson_admin(
    slug: str,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    lesson = db.query(models.Lesson).filter(models.Lesson.slug == slug).first()
    if not lesson:
        raise HTTPException(404, "Lecția nu există")
    return _lesson_admin_dict(db, lesson)


@router.patch("/lessons/{slug}")
def update_lesson(
    slug: str,
    data: schemas.LessonAdminUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    import json as _json

    from services import learn as learn_service

    lesson = db.query(models.Lesson).filter(models.Lesson.slug == slug).first()
    if not lesson:
        raise HTTPException(404, "Lecția nu există")

    payload = data.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(400, "Nimic de actualizat")

    for field in ("title", "summary", "icon", "video_url", "est_min"):
        if field in payload:
            setattr(lesson, field, payload[field])
    if "intro" in payload:
        lesson.content = payload["intro"]
    if "req_tier" in payload:
        # XP-ul e derivat din treaptă, deci se recalculează odată cu ea.
        lesson.req_tier = payload["req_tier"]
        lesson.xp = learn_service.xp_for_tier(lesson.req_tier)
        lesson.mastery_xp = learn_service.mastery_xp_for_tier(lesson.req_tier)
    for field in ("steps", "tips", "prereqs"):
        if field in payload:
            setattr(lesson, field, _json.dumps(payload[field], ensure_ascii=False))
    for field in ("quiz", "mastery_quiz"):
        if field in payload:
            questions = payload[field]
            for item in questions:
                if item["correct"] >= len(item["options"]):
                    raise HTTPException(
                        400, f"Răspunsul corect iese din lista de opțiuni: {item['q']}"
                    )
            setattr(lesson, field, _json.dumps(questions, ensure_ascii=False))

    lesson.custom = True
    db.commit()
    db.refresh(lesson)
    return _lesson_admin_dict(db, lesson)


@router.post("/lessons/{slug}/reset")
def reset_lesson(
    slug: str,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    """Renunță la editările manuale și re-aplică seed-ul pe această lecție."""
    from services import learn as learn_service

    lesson = db.query(models.Lesson).filter(models.Lesson.slug == slug).first()
    if not lesson:
        raise HTTPException(404, "Lecția nu există")
    lesson.custom = False
    db.commit()
    learn_service.seed_lessons(db)
    db.refresh(lesson)
    return _lesson_admin_dict(db, lesson)


# ---------- tabloul de bord ----------

def _since(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


def _count(db: Session, model, *filters) -> int:
    q = db.query(func.count(model.id))
    for f in filters:
        q = q.filter(f)
    return int(q.scalar() or 0)


def _daily_series(db: Session, model, days: int = 14) -> list:
    """Câte rânduri pe zi în ultimele `days` zile, inclusiv zilele goale.

    Numărăm în Python peste `created_at`: `date_trunc` e specific Postgres, iar
    dezvoltarea locală merge pe SQLite — o serie de două săptămâni e destul de
    mică încât diferența să nu conteze.
    """
    start = _since(days - 1).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(model.created_at)
        .filter(model.created_at >= start)
        .all()
    )
    buckets = {}
    for (created,) in rows:
        if created is None:
            continue
        buckets[created.date().isoformat()] = buckets.get(created.date().isoformat(), 0) + 1
    out = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date().isoformat()
        out.append({"date": day, "count": buckets.get(day, 0)})
    return out


@router.get("/stats")
def moderation_stats(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Ce se întâmplă în aplicație, pe o singură pagină.

    Consola avea doar cozi de lucru: puteai trata ce era în fața ta, dar nu
    vedeai dacă e o zi liniștită sau un val. Aici sunt totalurile, ce s-a
    întâmplat în ultimele 7 zile, cozile deschise și cine e activ.
    """
    week = _since(7)
    now = datetime.utcnow()

    users_total = _count(db, models.User)
    users_new = _count(db, models.User, models.User.created_at >= week)
    users_suspended = _count(db, models.User, models.User.suspended_until > now)
    users_inactive = _count(db, models.User, models.User.is_active == False)  # noqa: E712
    staff = _count(db, models.User, models.User.role.in_(("admin", "moderator")))

    recipes_total = _count(db, models.Recipe)
    recipes_new = _count(db, models.Recipe, models.Recipe.created_at >= week)
    recipes_flagged = _count(db, models.Recipe, models.Recipe.moderation_status == "flagged")
    recipes_hidden = _count(db, models.Recipe, models.Recipe.moderation_status == "hidden")

    posts_total = _count(db, models.ForumPost)
    posts_new = _count(db, models.ForumPost, models.ForumPost.created_at >= week)
    posts_hidden = _count(db, models.ForumPost, models.ForumPost.moderation_status == "hidden")
    comments_total = _count(db, models.ForumComment)

    reviews_total = _count(db, models.Review)
    reviews_new = _count(db, models.Review, models.Review.created_at >= week)
    cooks_verified = _count(
        db, models.SavedRecipe, models.SavedRecipe.cooked_verified == True  # noqa: E712
    )

    # Cine a scris ceva în ultima săptămână — proxy pentru „activ", fără un
    # tabel de sesiuni pe care oricum nu-l avem.
    active_authors = {
        row[0]
        for row in db.query(models.Recipe.author_id)
        .filter(models.Recipe.created_at >= week)
        .all()
    }
    active_authors |= {
        row[0]
        for row in db.query(models.Review.user_id)
        .filter(models.Review.created_at >= week)
        .all()
    }
    active_authors |= {
        row[0]
        for row in db.query(models.ForumPost.author_id)
        .filter(models.ForumPost.created_at >= week)
        .all()
    }
    active_authors.discard(None)

    top_recipes = (
        db.query(
            models.Recipe,
            func.coalesce(func.avg(models.Review.rating), 0).label("avg"),
            func.count(models.Review.id).label("n"),
        )
        .outerjoin(models.Review, models.Review.recipe_id == models.Recipe.id)
        .filter(models.Recipe.moderation_status == "ok")
        .group_by(models.Recipe.id)
        .having(func.count(models.Review.id) > 0)
        .order_by(func.avg(models.Review.rating).desc(), func.count(models.Review.id).desc())
        .limit(5)
        .all()
    )

    newest = (
        db.query(models.User)
        .order_by(models.User.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "generated_at": iso_utc(now),
        "totals": {
            "users": users_total,
            "recipes": recipes_total,
            "posts": posts_total,
            "comments": comments_total,
            "reviews": reviews_total,
            "cooks_verified": cooks_verified,
        },
        "week": {
            "users": users_new,
            "recipes": recipes_new,
            "posts": posts_new,
            "reviews": reviews_new,
            "active_people": len(active_authors),
        },
        "queues": {
            "flagged_recipes": recipes_flagged,
            "hidden_recipes": recipes_hidden,
            "hidden_posts": posts_hidden,
        },
        "accounts": {
            "suspended": users_suspended,
            "deactivated": users_inactive,
            "staff": staff,
        },
        "series": {
            "signups": _daily_series(db, models.User),
            "recipes": _daily_series(db, models.Recipe),
            "posts": _daily_series(db, models.ForumPost),
        },
        "top_recipes": [
            {
                "id": r.id,
                "title": r.title,
                "image_url": r.image_url or "",
                "avg_rating": round(float(avg or 0), 1),
                "review_count": int(n or 0),
                "author": serializers.author_mini(r.author),
            }
            for r, avg, n in top_recipes
        ],
        "newest_users": [
            {
                **serializers.author_mini(u),
                "role": u.role,
                "created_at": iso_utc(u.created_at),
            }
            for u in newest
        ],
    }
