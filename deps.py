"""Dependințe FastAPI partajate: autentificare cu bearer token."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

# Schema Bearer — FastAPI citește header-ul `Authorization: Bearer <token>`
# și afișează butonul "Authorize" în /docs.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Întoarce userul autentificat sau ridică 401."""
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
    """La fel ca get_current_user dar întoarce None în loc de 401.

    Util pentru rute publice care își schimbă răspunsul dacă ești logat
    (ex. `is_following` la search)."""
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
    """Doar moderator/admin."""
    if user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Necesită drepturi de moderator",
        )
    return user
