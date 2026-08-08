from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from database import get_db
import auth
import models

# creează toate tabelele în DB la pornire
Base.metadata.create_all(bind=engine)

# Migrări defensive: adaugă coloanele noi pe tabelele deja existente. Postgres
# suportă IF NOT EXISTS, deci e sigur să rulăm la fiecare pornire (înlocuiește
# lipsa unui tool de migrare tip Alembic).
_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS image_url VARCHAR DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS images TEXT DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS moderation_status VARCHAR DEFAULT 'ok'",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS ai_notes TEXT DEFAULT ''",
    "ALTER TABLE saved_recipes ADD COLUMN IF NOT EXISTS cooked_verified BOOLEAN DEFAULT FALSE",
    "ALTER TABLE saved_recipes ADD COLUMN IF NOT EXISTS cook_photo_url VARCHAR DEFAULT ''",
]
# Rulăm fiecare migrare izolat: o coloană care există deja (sau un dialect care
# nu suportă IF NOT EXISTS, ex. SQLite local) nu trebuie să blocheze pornirea.
for stmt in _MIGRATIONS:
    try:
        with engine.begin() as conn:
            conn.execute(text(stmt))
    except Exception:
        pass

app = FastAPI(title="Cooking App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://kookafrontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routere pe feature ----------
from routers import recipes, reviews, users, search, daily, uploads, admin

app.include_router(recipes.router)
app.include_router(reviews.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(daily.router)
app.include_router(uploads.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- Scheme pentru datele primite (request) ----------

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str


# ---------- Endpoint de login ----------

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parolă incorectă"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cont dezactivat. Contactează un administrator."
        )

    token = auth.create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Endpoint de "am uitat parola" ----------

@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        return {"exists": False, "message": "Nu există niciun cont cu acest email"}

    return {"exists": True, "message": "Emailul este corect, contul există"}

# ---------- Schema pentru datele de înregistrare ----------

class RegisterRequest(BaseModel):
    full_name: str = ""
    email: EmailStr
    username: str
    password: str
    password_confirm: str


# ---------- Endpoint de înregistrare ----------

@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.password != data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parolele nu coincid"
        )

    existing_user = db.query(models.User).filter(
        (models.User.email == data.email) | (models.User.username == data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Există deja un cont cu acest email sau username"
        )

    new_user = models.User(
        full_name=data.full_name,
        email=data.email,
        username=data.username,
        hashed_password=auth.hash_password(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth.create_token(new_user.id)
    return {"access_token": token, "token_type": "bearer"}
