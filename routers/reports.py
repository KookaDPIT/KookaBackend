"""Raportarea conținutului de către utilizatori.

Butonul „Report" exista pe rețete și pe forum și nu trimitea nimic nicăieri.
Acum scrie un rând într-o coadă pe care moderatorii o văd în consolă, alături
de cozile de rețete semnalate de AI și de postările ascunse.

Un raport per (om, obiect): a apăsa de trei ori nu înseamnă trei semnalări, dar
nici nu dă eroare — reîncadrăm raportul existent cu motivul nou, ca cineva care
s-a răzgândit asupra motivului să nu rămână blocat.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from deps import get_current_user, require_not_suspended
from services import reports as reports_service

router = APIRouter(tags=["reports"])


def _target_exists(db: Session, target_type: str, target_id: int) -> bool:
    if target_type == "recipe":
        return (
            db.query(models.Recipe).filter(models.Recipe.id == target_id).first()
            is not None
        )
    if target_type == "forum_post":
        return (
            db.query(models.ForumPost).filter(models.ForumPost.id == target_id).first()
            is not None
        )
    if target_type == "forum_comment":
        return (
            db.query(models.ForumComment)
            .filter(models.ForumComment.id == target_id)
            .first()
            is not None
        )
    return False


@router.get("/reports/reasons")
def report_reasons(target_type: str = ""):
    """Motivele valabile. Trimise de backend ca lista să fie una singură — ele
    sunt și cheile după care moderatorii filtrează coada."""
    return {"reasons": reports_service.table(target_type)}


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(
    data: schemas.ReportIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    _: models.User = Depends(require_not_suspended),
):
    target_type = (data.target_type or "").strip().lower()
    if target_type not in reports_service.TARGET_TYPES:
        raise HTTPException(400, "Tip de conținut necunoscut")
    if not _target_exists(db, target_type, data.target_id):
        raise HTTPException(404, "Conținutul nu există")

    reason = reports_service.normalize_reason(data.reason)
    details = (data.details or "").strip()[:1000]
    if reason == "other" and not details:
        raise HTTPException(400, "Spune pe scurt ce e în neregulă")

    existing = (
        db.query(models.Report)
        .filter(
            models.Report.reporter_id == user.id,
            models.Report.target_type == target_type,
            models.Report.target_id == data.target_id,
        )
        .first()
    )
    if existing is not None:
        # deja raportat: actualizăm motivul și îl redeschidem dacă fusese închis
        existing.reason = reason
        existing.details = details
        if existing.status != "open":
            existing.status = "open"
            existing.handled_by = None
            existing.handled_at = None
        db.commit()
        return {"ok": True, "already_reported": True}

    db.add(
        models.Report(
            reporter_id=user.id,
            target_type=target_type,
            target_id=data.target_id,
            reason=reason,
            details=details,
        )
    )
    db.commit()
    return {"ok": True, "already_reported": False}


@router.get("/reports/mine")
def my_reports(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Ce a raportat deja acest cont — interfața folosește asta ca să arate
    „Raportat" în loc să lase butonul să pară că n-a făcut nimic."""
    rows = (
        db.query(models.Report.target_type, models.Report.target_id)
        .filter(models.Report.reporter_id == user.id)
        .all()
    )
    return {"reported": [f"{t}:{i}" for t, i in rows]}
