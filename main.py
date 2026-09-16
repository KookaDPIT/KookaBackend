from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from fastapi import Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel, EmailStr
from database import get_db
import auth
import deps
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
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cover_url VARCHAR DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS settings TEXT DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS allergies TEXT DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS image_url VARCHAR DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS images TEXT DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS moderation_status VARCHAR DEFAULT 'ok'",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS ai_notes TEXT DEFAULT ''",
    # Limba în care a fost scrisă rețeta; conținutul salvat e mereu în engleză.
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS source_language VARCHAR DEFAULT 'en'",
    "ALTER TABLE saved_recipes ADD COLUMN IF NOT EXISTS cooked_verified BOOLEAN DEFAULT FALSE",
    "ALTER TABLE saved_recipes ADD COLUMN IF NOT EXISTS cook_photo_url VARCHAR DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_until TIMESTAMP",
    "ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'en'",
    "ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS tag VARCHAR DEFAULT 'question'",
    "ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0",
    "ALTER TABLE forum_posts ADD COLUMN IF NOT EXISTS moderation_status VARCHAR DEFAULT 'ok'",
    # ---- Learn: fagurele de lecții + rank-uri ----
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS rank VARCHAR DEFAULT 'copper'",
    "ALTER TABLE saved_recipes ADD COLUMN IF NOT EXISTS cooked_at TIMESTAMP",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS slug VARCHAR",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS branch VARCHAR DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS icon VARCHAR DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS summary TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS steps TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS tips TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS quiz TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS mastery_quiz TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS prereqs TEXT DEFAULT ''",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS req_tier INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS est_min INTEGER DEFAULT 20",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS mastery_xp INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS hex_q INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS hex_r INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS custom BOOLEAN DEFAULT FALSE",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS mastery_passed BOOLEAN DEFAULT FALSE",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS mastered BOOLEAN DEFAULT FALSE",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS mastered_at TIMESTAMP",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS mastery_attempts INTEGER DEFAULT 0",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS cooldown_until TIMESTAMP",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS mastery_cooldown_until TIMESTAMP",
    # Rețetele existente au doar easy/medium/hard — le mapăm o singură dată.
    "UPDATE recipes SET rank = 'copper'   WHERE (rank IS NULL OR rank = '') AND difficulty = 'easy'",
    "UPDATE recipes SET rank = 'silver'   WHERE (rank IS NULL OR rank = '') AND difficulty = 'medium'",
    "UPDATE recipes SET rank = 'platinum' WHERE (rank IS NULL OR rank = '') AND difficulty = 'hard'",
    "UPDATE recipes SET rank = 'copper'   WHERE rank IS NULL OR rank = ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS course VARCHAR DEFAULT ''",
    # ---- textul original al autorului, păstrat lângă traducere ----
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS original_title VARCHAR DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS original_description TEXT DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS original_ingredients TEXT DEFAULT ''",
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS original_steps TEXT DEFAULT ''",
    # ---- Istoricul gătirilor (cook_logs) ----
    # Tabela e creată de metadata.create_all; asta o populează O SINGURĂ DATĂ
    # din ce știam deja, ca streak-urile și trofeele să nu pornească de la zero
    # pentru conturile existente. `saved_recipes` reține doar ultima gătire per
    # rețetă, deci recuperăm o linie per pereche, nu istoricul complet — atât se
    # poate reconstrui onest. XP-ul trecut era 20 fix, indiferent de rank.
    """INSERT INTO cook_logs (user_id, recipe_id, rank, xp_awarded, times_cooked, cooked_at)
       SELECT s.user_id, s.recipe_id, COALESCE(r.rank, 'copper'), 20, 1, s.cooked_at
       FROM saved_recipes s JOIN recipes r ON r.id = s.recipe_id
       WHERE s.cooked_verified = TRUE AND s.cooked_at IS NOT NULL
         AND NOT EXISTS (SELECT 1 FROM cook_logs)""",
]
# Rulăm fiecare migrare izolat: o coloană care există deja (sau un dialect care
# nu suportă IF NOT EXISTS, ex. SQLite local) nu trebuie să blocheze pornirea.
for stmt in _MIGRATIONS:
    try:
        with engine.begin() as conn:
            conn.execute(text(stmt))
    except Exception:
        # SQLite (dezvoltarea locală) nu cunoaște `ADD COLUMN IF NOT EXISTS`, iar
        # fără a doua încercare coloanele noi pur și simplu nu apăreau acolo: pe
        # Render mergea, local rețetele rămâneau fără `course` și filtrul nou
        # dădea „no such column". Reîncercăm fără clauză; dacă pică și asta,
        # coloana chiar există deja (sau enunțul nu era un ADD COLUMN) și tăcem
        # ca înainte.
        retry = stmt.replace(" IF NOT EXISTS", "") if "IF NOT EXISTS" in stmt else ""
        if not retry:
            continue
        try:
            with engine.begin() as conn:
                conn.execute(text(retry))
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
from routers import (
    recipes, reviews, users, search, daily, uploads, admin, forum, learn, ai,
    bookmarks, cooking,
    planner, reports,
)

app.include_router(learn.router)
app.include_router(recipes.router)
app.include_router(reviews.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(bookmarks.router)
app.include_router(cooking.router)
app.include_router(daily.router)
app.include_router(uploads.router)
app.include_router(admin.router)
app.include_router(forum.router)
app.include_router(ai.router)
app.include_router(planner.router)
app.include_router(reports.router)

# Cele 50 de lecții vin din `data/lessons_seed.py` și se rescriu la fiecare
# pornire, ca modificările de conținut să ajungă în DB fără migrare manuală.
# Lecțiile editate din /admin sunt marcate `custom` și rămân neatinse.
try:
    from database import SessionLocal
    from services import learn as learn_service

    _seed_db = SessionLocal()
    try:
        learn_service.seed_lessons(_seed_db)
    finally:
        _seed_db.close()
except Exception as exc:  # pornirea nu trebuie blocată de seed
    print(f"[learn] seed sărit: {exc}")


# Rețetele de dinaintea coloanei `course` nu au tip, deci n-ar apărea sub niciun
# filtru de tip — filtrul ar debuta pe un catalog care pare gol. Le clasificăm
# o dată, euristic (services/courses.guess). Analizorul AI e mai bun și le
# rescrie la următorul „recalculează"; asta e doar ca pornirea să nu fie goală.
try:
    from database import SessionLocal
    from services import courses as courses_service
    import serializers as _serializers

    _course_db = SessionLocal()
    try:
        pending = (
            _course_db.query(models.Recipe)
            .filter((models.Recipe.course == "") | (models.Recipe.course.is_(None)))
            .all()
        )
        for _r in pending:
            _r.course = courses_service.guess(
                _r.title,
                _serializers._load_json(_r.ingredients, []),
                _r.description or "",
            )
        if pending:
            _course_db.commit()
            print(f"[courses] {len(pending)} recipes classified heuristically")
    finally:
        _course_db.close()
except Exception as exc:
    print(f"[courses] backfill skipped: {exc}")


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- OCR pentru date de expirare ----------
# Tesseract rulează în container (vezi Dockerfile). Dacă binarul lipsește —
# rulare locală fără Docker — endpointul întoarce 503, restul aplicației merge.

MAX_OCR_UPLOAD = 8 * 1024 * 1024  # 8 MB; peste asta consumăm RAM degeaba


@app.get("/ocr/health")
def ocr_health():
    """Verifică dacă binarul Tesseract e disponibil în container."""
    try:
        import pytesseract

        return {"available": True, "version": str(pytesseract.get_tesseract_version())}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@app.post("/ocr/expiry")
async def ocr_expiry(
    file: UploadFile = File(...),
    viewer: models.User = Depends(deps.get_current_user_optional),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fișierul trebuie să fie o imagine",
        )

    raw = await file.read()
    if len(raw) > MAX_OCR_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Imaginea depășește 8 MB",
        )

    # Import întârziat: fără el, lipsa lui pytesseract/Pillow ar bloca pornirea
    # întregii aplicații, nu doar acest endpoint.
    try:
        from ocr import read_expiry
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OCR indisponibil: {exc}",
        )

    try:
        return read_expiry(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR a eșuat: {exc}",
        )


# ---------- Scheme pentru datele primite (request) ----------

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str


# ---------- Endpoint de login ----------

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # emailurile se stochează lowercase la înregistrare — căutăm la fel, ca un
    # login scris cu majuscule să nu pice degeaba
    user = db.query(models.User).filter(
        func.lower(models.User.email) == data.email.strip().lower()
    ).first()

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

    token = auth.create_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Endpoint de "am uitat parola" ----------

@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        func.lower(models.User.email) == data.email.strip().lower()
    ).first()

    if not user:
        return {"exists": False, "message": "Nu există niciun cont cu acest email"}

    return {"exists": True, "message": "Emailul este corect, contul există"}

# ---------- Disponibilitate username / email ----------

def _username_taken(db: Session, username: str, except_id: int = None) -> bool:
    """Comparație case-insensitive: `Alex` și `alex` sunt același handle."""
    if not username:
        return False
    q = db.query(models.User).filter(
        func.lower(models.User.username) == username.strip().lstrip("@").lower()
    )
    if except_id is not None:
        q = q.filter(models.User.id != except_id)
    return q.first() is not None


def _email_taken(db: Session, email: str, except_id: int = None) -> bool:
    if not email:
        return False
    q = db.query(models.User).filter(
        func.lower(models.User.email) == email.strip().lower()
    )
    if except_id is not None:
        q = q.filter(models.User.id != except_id)
    return q.first() is not None


@app.get("/auth/availability")
def check_availability(
    username: str = "",
    email: str = "",
    db: Session = Depends(get_db),
    viewer: models.User = Depends(deps.get_current_user_optional),
):
    """Verificare live pentru formularul de înregistrare ȘI pentru ecranul de
    setări. Dacă apelantul e autentificat, propriul cont e exclus din verificare
    — altfel ți-ai vedea propriul username raportat drept „ocupat" de îndată ce
    deschizi setările. Întoarce doar booleeni, niciodată cui aparține contul."""
    except_id = viewer.id if viewer is not None else None
    result = {}
    if username.strip():
        result["username_taken"] = _username_taken(db, username, except_id)
    if email.strip():
        result["email_taken"] = _email_taken(db, email, except_id)
    return result


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

    username = data.username.strip().lstrip("@")
    email = data.email.strip().lower()

    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Numele de utilizator nu poate fi gol"
        )

    # Verificări separate, ca frontend-ul să știe exact ce câmp e ocupat.
    if _username_taken(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acest nume de utilizator este deja folosit"
        )

    if _email_taken(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Există deja un cont cu acest email"
        )

    new_user = models.User(
        full_name=data.full_name,
        email=email,
        username=username,
        hashed_password=auth.hash_password(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth.create_token(new_user.id, new_user.role)
    return {"access_token": token, "token_type": "bearer"}