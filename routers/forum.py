"""Forum: subforumuri pe limbă, taguri pentru subiect, voturi și comentarii.

Model de organizare: un singur forum împărțit în subforumuri **după limba în
care scrii** (`language`). Subiectul unei postări nu mai e un subforum separat,
ci un `tag` — așa același subiect e găsibil în toate limbile, iar cititorul
alege întâi limba pe care o înțelege.
"""
import json
import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
import serializers
from serializers import iso_utc
from database import get_db
from deps import (
    ROLE_LEVELS,
    get_current_user,
    get_current_user_optional,
    require_not_suspended,
)
from services import visibility

router = APIRouter(prefix="/forum", tags=["forum"])

# Catalogul complet ISO 639-1 (toate cele 184 de coduri). Eticheta în engleză e
# doar rezervă: interfața afișează numele limbii tradus, prin Intl.DisplayNames.
LANGUAGE_NAMES = {
    "aa": "Afar", "ab": "Abkhazian", "ae": "Avestan", "af": "Afrikaans",
    "ak": "Akan", "am": "Amharic", "an": "Aragonese", "ar": "Arabic",
    "as": "Assamese", "av": "Avaric", "ay": "Aymara", "az": "Azerbaijani",
    "ba": "Bashkir", "be": "Belarusian", "bg": "Bulgarian", "bi": "Bislama",
    "bm": "Bambara", "bn": "Bengali", "bo": "Tibetan", "br": "Breton",
    "bs": "Bosnian", "ca": "Catalan", "ce": "Chechen", "ch": "Chamorro",
    "co": "Corsican", "cr": "Cree", "cs": "Czech", "cu": "Church Slavic",
    "cv": "Chuvash", "cy": "Welsh", "da": "Danish", "de": "German",
    "dv": "Divehi", "dz": "Dzongkha", "ee": "Ewe", "el": "Greek",
    "en": "English", "eo": "Esperanto", "es": "Spanish", "et": "Estonian",
    "eu": "Basque", "fa": "Persian", "ff": "Fulah", "fi": "Finnish",
    "fj": "Fijian", "fo": "Faroese", "fr": "French", "fy": "Western Frisian",
    "ga": "Irish", "gd": "Scottish Gaelic", "gl": "Galician", "gn": "Guarani",
    "gu": "Gujarati", "gv": "Manx", "ha": "Hausa", "he": "Hebrew",
    "hi": "Hindi", "ho": "Hiri Motu", "hr": "Croatian", "ht": "Haitian Creole",
    "hu": "Hungarian", "hy": "Armenian", "hz": "Herero", "ia": "Interlingua",
    "id": "Indonesian", "ie": "Interlingue", "ig": "Igbo", "ii": "Sichuan Yi",
    "ik": "Inupiaq", "io": "Ido", "is": "Icelandic", "it": "Italian",
    "iu": "Inuktitut", "ja": "Japanese", "jv": "Javanese", "ka": "Georgian",
    "kg": "Kongo", "ki": "Kikuyu", "kj": "Kuanyama", "kk": "Kazakh",
    "kl": "Kalaallisut", "km": "Khmer", "kn": "Kannada", "ko": "Korean",
    "kr": "Kanuri", "ks": "Kashmiri", "ku": "Kurdish", "kv": "Komi",
    "kw": "Cornish", "ky": "Kyrgyz", "la": "Latin", "lb": "Luxembourgish",
    "lg": "Ganda", "li": "Limburgish", "ln": "Lingala", "lo": "Lao",
    "lt": "Lithuanian", "lu": "Luba-Katanga", "lv": "Latvian", "mg": "Malagasy",
    "mh": "Marshallese", "mi": "Maori", "mk": "Macedonian", "ml": "Malayalam",
    "mn": "Mongolian", "mr": "Marathi", "ms": "Malay", "mt": "Maltese",
    "my": "Burmese", "na": "Nauru", "nb": "Norwegian Bokmal", "nd": "North Ndebele",
    "ne": "Nepali", "ng": "Ndonga", "nl": "Dutch", "nn": "Norwegian Nynorsk",
    "no": "Norwegian", "nr": "South Ndebele", "nv": "Navajo", "ny": "Nyanja",
    "oc": "Occitan", "oj": "Ojibwa", "om": "Oromo", "or": "Odia",
    "os": "Ossetian", "pa": "Punjabi", "pi": "Pali", "pl": "Polish",
    "ps": "Pashto", "pt": "Portuguese", "qu": "Quechua", "rm": "Romansh",
    "rn": "Rundi", "ro": "Romanian", "ru": "Russian", "rw": "Kinyarwanda",
    "sa": "Sanskrit", "sc": "Sardinian", "sd": "Sindhi", "se": "Northern Sami",
    "sg": "Sango", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian",
    "sm": "Samoan", "sn": "Shona", "so": "Somali", "sq": "Albanian",
    "sr": "Serbian", "ss": "Swati", "st": "Southern Sotho", "su": "Sundanese",
    "sv": "Swedish", "sw": "Swahili", "ta": "Tamil", "te": "Telugu",
    "tg": "Tajik", "th": "Thai", "ti": "Tigrinya", "tk": "Turkmen",
    "tl": "Tagalog", "tn": "Tswana", "to": "Tongan", "tr": "Turkish",
    "ts": "Tsonga", "tt": "Tatar", "tw": "Twi", "ty": "Tahitian",
    "ug": "Uyghur", "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek",
    "ve": "Venda", "vi": "Vietnamese", "vo": "Volapuk", "wa": "Walloon",
    "wo": "Wolof", "xh": "Xhosa", "yi": "Yiddish", "yo": "Yoruba",
    "za": "Zhuang", "zh": "Chinese", "zu": "Zulu",
}

LANGUAGES = [{"code": code, "label": name} for code, name in sorted(LANGUAGE_NAMES.items())]
LANGUAGE_CODES = set(LANGUAGE_NAMES)

# Vocabular fix de taguri — cu text liber, „help" / „Help" / „ajutor" ar sparge
# filtrarea în bucăți care nu se mai regăsesc.
TAGS = [
    {"code": "question", "emoji": "❓"},
    {"code": "recipe", "emoji": "📖"},
    {"code": "tip", "emoji": "💡"},
    {"code": "help", "emoji": "🆘"},
    {"code": "win", "emoji": "🏆"},
    {"code": "showcase", "emoji": "✨"},
    {"code": "gear", "emoji": "🔪"},
    {"code": "offtopic", "emoji": "💬"},
]
TAG_CODES = {x["code"] for x in TAGS}

SORTS = ("hot", "new", "top", "rising")


# ==========================================================================
#  Scoruri
# ==========================================================================
def _age_hours(post: models.ForumPost) -> float:
    created = post.created_at or datetime.utcnow()
    return max(0.0, (datetime.utcnow() - created).total_seconds() / 3600.0)


def _hot_score(post: models.ForumPost, comments: int) -> float:
    """Gravity decay în stil Hacker News: voturile și discuția ridică postarea,
    vârsta o coboară, ca prima pagină să nu înghețe pe un hit vechi."""
    weight = (post.votes or 0) + 2 * comments
    return (weight + 1) / math.pow(_age_hours(post) + 2, 1.5)


def _rising_score(post: models.ForumPost, comments: int) -> float:
    """Viteză, nu total: cât a strâns pe oră de când a apărut. Doar postările
    proaspete concurează, altfel „rising" ar fi doar „top" cu alt nume."""
    hours = _age_hours(post)
    if hours > 48:
        return -1.0
    return ((post.votes or 0) + 2 * comments) / (hours + 1)


# ==========================================================================
#  Serializare
# ==========================================================================
def _comment_counts(db: Session, post_ids):
    if not post_ids:
        return {}
    rows = (
        db.query(models.ForumComment.post_id, func.count(models.ForumComment.id))
        .filter(models.ForumComment.post_id.in_(post_ids))
        .group_by(models.ForumComment.post_id)
        .all()
    )
    return {pid: int(n) for pid, n in rows}


def _my_votes(db: Session, viewer, post_ids):
    if viewer is None or not post_ids:
        return {}
    rows = (
        db.query(models.ForumVote.post_id, models.ForumVote.value)
        .filter(
            models.ForumVote.user_id == viewer.id,
            models.ForumVote.post_id.in_(post_ids),
        )
        .all()
    )
    return {pid: int(v) for pid, v in rows}


def _images(post) -> list:
    """Lista de poze a postării. Coloana e text JSON și poate lipsi cu totul pe
    rândurile scrise înainte de migrare, deci nimic din ce vine de acolo nu e
    de încredere fără verificare."""
    raw = getattr(post, "images", "") or ""
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(u) for u in parsed if u]


def _clean_images(urls) -> list:
    """Cel mult 6 URL-uri, fără goluri. Limita ține tile-ul și payload-ul mici;
    o postare care are nevoie de mai mult de șase poze are nevoie de un album."""
    out = []
    for u in (urls or [])[:6]:
        u = str(u).strip()
        if u:
            out.append(u)
    return out


def _post_to_dict(post, comments=0, my_vote=0, with_body=False):
    data = {
        "id": post.id,
        "is_hidden": (post.moderation_status or "ok") == "hidden",
        "title": post.title,
        "language": post.language or "en",
        "tag": post.tag or "question",
        "images": _images(post),
        "votes": post.votes or 0,
        "views": post.views or 0,
        "comment_count": comments,
        "my_vote": my_vote,
        "author": serializers.author_mini(post.author),
        "created_at": iso_utc(post.created_at),
    }
    # în listă trimitem doar un fragment: tile-urile afișează cel mult 2-3 rânduri
    body = post.body or ""
    data["excerpt"] = body[:180] + ("…" if len(body) > 180 else "")
    if with_body:
        data["body"] = body
    return data


def _comment_to_dict(c, viewer=None):
    return {
        "id": c.id,
        "body": c.body or "",
        "parent_id": c.parent_id,
        "author": serializers.author_mini(c.author),
        "created_at": iso_utc(c.created_at),
        "is_mine": viewer is not None and c.author_id == viewer.id,
    }


def _can_moderate(user) -> bool:
    return user is not None and ROLE_LEVELS.get(user.role, 0) >= ROLE_LEVELS["moderator"]


# ==========================================================================
#  Meta (subforumuri, taguri, tendințe)
# ==========================================================================
@router.get("/meta")
def meta(
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    """Tot ce are nevoie interfața ca să deseneze filtrele: limbile cu numărul
    de postări, tagurile, și tagurile în tendință din ultimele 7 zile."""
    # numărătorile trebuie să reflecte ce se poate chiar deschide, altfel un
    # subforum arată „3 postări" și se deschide gol
    visible = visibility.visible_authors(
        db.query(models.ForumPost).filter(models.ForumPost.moderation_status == "ok"),
        models.ForumPost,
        visibility.hidden_author_ids(db, viewer),
    ).subquery()

    lang_rows = dict(
        db.query(visible.c.language, func.count(visible.c.id))
        .group_by(visible.c.language)
        .all()
    )
    tag_rows = dict(
        db.query(visible.c.tag, func.count(visible.c.id))
        .group_by(visible.c.tag)
        .all()
    )

    since = datetime.utcnow() - timedelta(days=7)
    trending_rows = (
        db.query(
            visible.c.tag,
            func.count(visible.c.id).label("n"),
            func.coalesce(func.sum(visible.c.votes), 0).label("v"),
        )
        .filter(visible.c.created_at >= since)
        .group_by(visible.c.tag)
        .order_by(func.count(visible.c.id).desc())
        .limit(5)
        .all()
    )

    # `languages` = subforumurile care chiar există (au cel puțin o postare),
    # cele mai populate primele. `all_languages` e catalogul întreg, pentru
    # selectorul din care poți deschide un subforum nou în orice limbă.
    active = sorted(
        (
            {"code": code, "label": LANGUAGE_NAMES.get(code, code), "posts": int(n or 0)}
            for code, n in lang_rows.items()
            if code in LANGUAGE_CODES and (n or 0) > 0
        ),
        key=lambda x: (-x["posts"], x["label"]),
    )

    return {
        "languages": active,
        "all_languages": LANGUAGES,
        "tags": [
            {**tag, "posts": int(tag_rows.get(tag["code"], 0) or 0)}
            for tag in TAGS
        ],
        "trending": [
            {"tag": tag, "posts": int(n or 0), "votes": int(v or 0)}
            for tag, n, v in trending_rows
        ],
        "total": int(db.query(func.count(visible.c.id)).scalar() or 0),
    }


# ==========================================================================
#  Listare + căutare
# ==========================================================================
@router.get("/posts")
def list_posts(
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
    q: str = Query("", description="ID-ul postării sau cuvinte din titlu"),
    language: str = Query("", description="codul subforumului"),
    tag: str = Query(""),
    sort: str = Query("hot", description="hot | new | top | rising"),
    limit: int = Query(60, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if sort not in SORTS:
        raise HTTPException(400, f"Sortare invalidă. Alege dintre: {', '.join(SORTS)}")

    query = db.query(models.ForumPost).filter(
        models.ForumPost.moderation_status == "ok"
    )
    query = visibility.visible_authors(
        query, models.ForumPost, visibility.hidden_author_ids(db, viewer)
    )

    term = q.strip()
    if term:
        # Un termen numeric e căutare după ID — e singurul mod de a nimeri exact
        # o postare al cărei titlu nu ți-l amintești. Restul caută în titlu.
        if term.lstrip("#").isdigit():
            query = query.filter(models.ForumPost.id == int(term.lstrip("#")))
        else:
            query = query.filter(func.lower(models.ForumPost.title).like(f"%{term.lower()}%"))

    # O căutare după ID trece peste filtre: altfel ai da ID-ul corect și ai
    # primi „niciun rezultat" doar pentru că ești pe alt subforum.
    id_lookup = bool(term) and term.lstrip("#").isdigit()
    if not id_lookup:
        if language.strip():
            query = query.filter(models.ForumPost.language == language.strip())
        if tag.strip():
            query = query.filter(models.ForumPost.tag == tag.strip())

    rows = query.all()
    ids = [p.id for p in rows]
    counts = _comment_counts(db, ids)
    mine = _my_votes(db, viewer, ids)

    if sort == "new":
        rows.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
    elif sort == "top":
        rows.sort(key=lambda p: (p.votes or 0, p.created_at or datetime.min), reverse=True)
    elif sort == "rising":
        rows = [p for p in rows if _rising_score(p, counts.get(p.id, 0)) >= 0]
        rows.sort(key=lambda p: _rising_score(p, counts.get(p.id, 0)), reverse=True)
    else:  # hot
        rows.sort(key=lambda p: _hot_score(p, counts.get(p.id, 0)), reverse=True)

    total = len(rows)
    page = rows[offset: offset + limit]
    return {
        "total": total,
        "posts": [
            _post_to_dict(p, counts.get(p.id, 0), mine.get(p.id, 0)) for p in page
        ],
    }


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    viewer: models.User = Depends(get_current_user_optional),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")

    staff = _can_moderate(viewer)
    mine = viewer is not None and post.author_id == viewer.id
    if (post.moderation_status or "ok") == "hidden" and not (staff or mine):
        raise HTTPException(404, "Postarea nu există")
    if post.author_id in visibility.hidden_author_ids(db, viewer):
        raise HTTPException(404, "Postarea nu există")

    post.views = (post.views or 0) + 1
    db.commit()

    # blocarea taie și comentariile — vezi services/visibility.py
    hidden_authors = visibility.hidden_author_ids(db, viewer)
    comment_query = db.query(models.ForumComment).filter(
        models.ForumComment.post_id == post_id
    )
    if hidden_authors:
        comment_query = comment_query.filter(
            models.ForumComment.author_id.notin_(hidden_authors)
        )
    comments = comment_query.order_by(models.ForumComment.created_at.asc()).all()
    mine = _my_votes(db, viewer, [post_id])
    data = _post_to_dict(post, len(comments), mine.get(post_id, 0), with_body=True)
    data["comments"] = [_comment_to_dict(c, viewer) for c in comments]
    data["can_edit"] = mine
    data["can_delete"] = mine or staff
    data["can_moderate"] = staff
    return data


# ==========================================================================
#  Creare / editare / ștergere
# ==========================================================================
@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(
    data: schemas.ForumPostCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_not_suspended),
):
    title = data.title.strip()
    if len(title) < 5:
        raise HTTPException(400, "Titlul trebuie să aibă cel puțin 5 caractere")
    if data.language not in LANGUAGE_CODES:
        raise HTTPException(400, "Alege un subforum (limbă) valid")
    if data.tag not in TAG_CODES:
        raise HTTPException(400, "Alege un tag valid")

    post = models.ForumPost(
        title=title,
        body=data.body.strip(),
        language=data.language,
        tag=data.tag,
        images=json.dumps(_clean_images(data.images), ensure_ascii=False),
        votes=1,                      # autorul își votează implicit postarea
        views=0,
        author_id=user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    db.add(models.ForumVote(user_id=user.id, post_id=post.id, value=1))
    user.xp_total = (user.xp_total or 0) + 10
    db.commit()

    return _post_to_dict(post, 0, 1, with_body=True)


@router.patch("/posts/{post_id}")
def update_post(
    post_id: int,
    data: schemas.ForumPostUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_not_suspended),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    if post.author_id != user.id:
        raise HTTPException(403, "Poți edita doar propriile postări")

    payload = data.model_dump(exclude_none=True)
    if "language" in payload and payload["language"] not in LANGUAGE_CODES:
        raise HTTPException(400, "Subforum invalid")
    if "tag" in payload and payload["tag"] not in TAG_CODES:
        raise HTTPException(400, "Tag invalid")
    if "title" in payload:
        payload["title"] = payload["title"].strip()
        if len(payload["title"]) < 5:
            raise HTTPException(400, "Titlul trebuie să aibă cel puțin 5 caractere")

    # `images` ajunge în DB ca text JSON, nu ca listă Python — restul câmpurilor
    # sunt coloane simple și merg prin setattr ca până acum.
    if "images" in payload:
        payload["images"] = json.dumps(_clean_images(payload["images"]), ensure_ascii=False)

    for field, value in payload.items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)

    counts = _comment_counts(db, [post.id])
    mine = _my_votes(db, user, [post.id])
    return _post_to_dict(post, counts.get(post.id, 0), mine.get(post.id, 0), with_body=True)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    if post.author_id != user.id and not _can_moderate(user):
        raise HTTPException(403, "Poți șterge doar propriile postări")

    db.query(models.ForumComment).filter(models.ForumComment.post_id == post_id).delete()
    db.query(models.ForumVote).filter(models.ForumVote.post_id == post_id).delete()
    db.delete(post)
    db.commit()


# ==========================================================================
#  Voturi
# ==========================================================================
@router.post("/posts/{post_id}/vote")
def vote(
    post_id: int,
    data: schemas.ForumVoteIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_not_suspended),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")

    existing = (
        db.query(models.ForumVote)
        .filter(models.ForumVote.user_id == user.id, models.ForumVote.post_id == post_id)
        .first()
    )
    previous = existing.value if existing else 0
    # Apăsarea aceleiași săgeți retrage votul, ca peste tot.
    new_value = 0 if data.value == previous else data.value

    if new_value == 0:
        if existing:
            db.delete(existing)
    elif existing:
        existing.value = new_value
    else:
        db.add(models.ForumVote(user_id=user.id, post_id=post_id, value=new_value))

    post.votes = (post.votes or 0) + (new_value - previous)
    db.commit()

    return {"votes": post.votes, "my_vote": new_value}


# ==========================================================================
#  Comentarii
# ==========================================================================
@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    data: schemas.ForumCommentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_not_suspended),
):
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")
    body = data.body.strip()
    if not body:
        raise HTTPException(400, "Comentariul nu poate fi gol")

    if data.parent_id is not None:
        parent = (
            db.query(models.ForumComment)
            .filter(
                models.ForumComment.id == data.parent_id,
                models.ForumComment.post_id == post_id,
            )
            .first()
        )
        if not parent:
            raise HTTPException(400, "Comentariul la care răspunzi nu există")

    comment = models.ForumComment(
        body=body,
        post_id=post_id,
        parent_id=data.parent_id,
        author_id=user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_to_dict(comment, user)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    comment = (
        db.query(models.ForumComment)
        .filter(models.ForumComment.id == comment_id)
        .first()
    )
    if not comment:
        raise HTTPException(404, "Comentariul nu există")
    if comment.author_id != user.id and not _can_moderate(user):
        raise HTTPException(403, "Poți șterge doar propriile comentarii")
    db.delete(comment)
    db.commit()


@router.post("/posts/{post_id}/moderate")
def moderate_post(
    post_id: int,
    data: schemas.ModerationAction,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Ascunde / repune o postare direct din thread, fără drum prin consolă."""
    if not _can_moderate(user):
        raise HTTPException(403, "Necesită drepturi de moderator")
    post = db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Postarea nu există")

    if data.action == "hide":
        post.moderation_status = "hidden"
    elif data.action == "restore":
        post.moderation_status = "ok"
    else:
        raise HTTPException(400, "Acțiune invalidă")
    db.commit()
    return {"moderation_status": post.moderation_status}
