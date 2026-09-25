import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
import bcrypt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
# 30 de zile. La 24 de ore, oricine deschidea aplicația a doua zi găsea
# ecranul de autentificare. Pentru o aplicație de bucătărie, costul unei
# reautentificări zilnice e mai mare decât riscul.
TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

# --- parole ---
def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    plain_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(plain_bytes, hashed.encode("utf-8"))

# --- token-uri ---
def create_token(user_id: int, role: str = "user") -> str:
    """Token JWT valabil TOKEN_EXPIRE_MINUTES.

    Poartă și rolul, ca frontend-ul să ascundă uneltele de moderare fără un
    request în plus. Rolul din token nu dă drepturi: deps.require_role recitește
    userul din DB la fiecare cerere, deci coloana rămâne sursa adevărului.
    """
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role or "user", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None