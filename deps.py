"""Dependințe FastAPI partajate: cine ești și ce ai voie.

Ordinea de la permisiv la restrictiv:
  get_current_user_optional  None când nu ești logat, pentru rute publice
  get_current_user           401 fără token valid
  require_not_suspended      403 cât timp sancțiunea e activă, pentru scrieri
  get_current_admin          moderator sau admin
  require_role("admin")      prag explicit de rol, vezi ROLE_LEVELS
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import auth
import models
from database import get_db
from datetime import datetime
# FastAPI citește header-ul `Authorization: Bearer <token>` și afișează
# butonul "Authorize" în /docs. auto_error=False lasă varianta optional
# să întoarcă None în loc să arunce.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Userul autentificat, sau 401. Conturile dezactivate primesc 403."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentificare necesară",
        )

    user_id = auth.decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid sau expirat",
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizatorul nu există",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cont dezactivat",
        )
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """La fel ca get_current_user, dar întoarce None în loc de 401.

    Pentru rutele publice care își schimbă răspunsul când ești logat, de pildă
    `is_following` la căutare sau `locked` pe carduri.
    """
    if credentials is None:
        return None
    user_id = auth.decode_token(credentials.credentials)
    if user_id is None:
        return None
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


def get_current_admin(
    user: models.User = Depends(get_current_user),
) -> models.User:
    """Doar moderator sau admin. Pentru praguri mai fine, require_role."""
    if user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Necesită drepturi de moderator",
        )
    return user

ROLE_LEVELS = {"user": 1, "moderator": 2, "admin": 3}


def require_role(min_role: str):
    """Fabrică de dependințe: cere rolul minim dat.

    Pe endpoint: Depends(deps.require_role("admin")).
    """
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if ROLE_LEVELS.get(user.role, 0) < ROLE_LEVELS.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nu ai permisiunea necesară",
            )
        return user
    return checker


def require_not_suspended(
    user: models.User = Depends(get_current_user),
) -> models.User:
    """403 cât timp `suspended_until` e în viitor.

    Se pune pe scrieri, nu pe citiri: un cont suspendat poate citi aplicația.
    """
    if user.suspended_until and user.suspended_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cont suspendat până la {user.suspended_until.strftime('%d.%m.%Y %H:%M')} UTC",
        )
    return user
