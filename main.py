from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import auth
import models

# creează toate tabelele în DB la pornire
Base.metadata.create_all(bind=engine)

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

    token = auth.create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Endpoint de "am uitat parola" ----------

@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        return {"exists": False, "message": "Nu există niciun cont cu acest email"}

    return {"exists": True, "message": "Emailul este corect, contul există"}