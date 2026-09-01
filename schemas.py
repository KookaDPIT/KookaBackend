"""Scheme Pydantic pentru request/response.

Notă: câmpurile stocate ca JSON în DB (ingredients, steps, nutrition,
allergens, images) sunt serializate/deserializate în routere, așa că aici
răspunsurile complexe folosesc tipuri Python native (list/dict)."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------- RECIPES ----------
class StepIn(BaseModel):
    text: str
    timer: Optional[str] = None   # ex. "8:30"
    label: Optional[str] = None


class RecipeCreate(BaseModel):
    title: str
    description: str = ""
    origin: str = ""                       # țara de origine
    servings: int = 1
    duration_min: int = 0
    difficulty: str = "easy"
    ingredients: List[str] = Field(default_factory=list)
    steps: List[StepIn] = Field(default_factory=list)
    image_url: str = ""                    # cover (deja urcat pe ImageKit)
    images: List[str] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    servings: Optional[int] = None
    duration_min: Optional[int] = None
    difficulty: Optional[str] = None
    ingredients: Optional[List[str]] = None
    steps: Optional[List[StepIn]] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None


# ---------- REVIEWS ----------
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    photo_url: str = ""


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    photo_url: Optional[str] = None


class CookVerifyRequest(BaseModel):
    cook_photo_url: str


# ---------- USERS / PROFILE ----------
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    units: Optional[str] = None
    settings: Optional[str] = None   # JSON serializat cu preferințele de client


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=72)


# ---------- MODERARE / ROLURI ----------
class RoleUpdate(BaseModel):
    role: str   # user / moderator / admin


class SuspendRequest(BaseModel):
    """Durata se dă în ore, ca să fie posibile și sancțiunile scurte (o zi,
    câteva ore). `days` rămâne pentru compatibilitate cu apelurile vechi."""
    days: int = Field(default=7, ge=1, le=3650)
    hours: Optional[int] = Field(default=None, ge=1, le=87600)


# ---------- FORUM ----------
class ForumPostCreate(BaseModel):
    title: str
    body: str = ""
    language: str = "en"     # subforumul
    tag: str = "question"    # subiectul


class ForumPostUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    language: Optional[str] = None
    tag: Optional[str] = None


class ForumVoteIn(BaseModel):
    value: int = Field(ge=-1, le=1)   # 1 up, -1 down, 0 retrage votul


class ForumCommentCreate(BaseModel):
    body: str
    parent_id: Optional[int] = None


class ActivityRef(BaseModel):
    kind: str          # created | reviewed | cooked
    entry_id: int


class ModerationAction(BaseModel):
    action: str        # hide | restore
