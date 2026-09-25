"""Citirea datei de expirare de pe ambalaj, cu Tesseract.

Fluxul, în ordinea din fișier:
  preprocess()     curăță poza pentru OCR
  extract_text()   textul brut, din trei treceri Tesseract
  PATTERNS         tiparele de dată, de la cel mai specific la cel mai larg
  parse_expiry()   alege data cea mai plauzibilă dintre potriviri
  read_expiry()    intrarea folosită de endpoint, le leagă pe toate

Fără opencv și fără numpy, doar Pillow, ca imaginea să rămână mică pe Render
Free. Binarul Tesseract vine din Dockerfile. Lipsa lui dă 503 pe endpoint,
restul aplicației merge mai departe.
"""

import calendar
import io
import re
from datetime import date

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

# Tesseract citește mult mai bine la text de cel puțin 30px înălțime.
MIN_WIDTH = 1200
MAX_WIDTH = 2400

LUNI = {
    "ian": 1, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mai": 5, "may": 5,
    "iun": 6, "jun": 6, "iul": 7, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "noi": 11, "nov": 11, "dec": 12,
}


def preprocess(raw: bytes) -> Image.Image:
    """Grayscale, contrast, redimensionare, binarizare.

    Face diferența pe text inkjet, care e cazul obișnuit pe ambalaje.
    """
    img = Image.open(io.BytesIO(raw))

    # Telefoanele salvează orientarea în EXIF. Fără asta, poza vine culcată.
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")

    w, h = img.size
    if w < MIN_WIDTH:
        scale = MIN_WIDTH / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    elif w > MAX_WIDTH:
        scale = MAX_WIDTH / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    # Prag fix la 140. Pe etichete lucioase bate media imaginii, care e trasă
    # în sus de reflexii.
    img = img.point(lambda p: 255 if p > 140 else 0, mode="1")
    return img


def extract_text(raw: bytes) -> str:
    """Textul brut, din trei treceri Tesseract: bloc, linie unică, text rar.

    Rezultatele se concatenează. O dată prinsă de o singură trecere e tot o
    dată găsită.
    """
    img = preprocess(raw)
    out = []
    for psm in (6, 7, 11):
        try:
            txt = pytesseract.image_to_string(img, lang="ron+eng", config=f"--oem 3 --psm {psm}")
            if txt.strip():
                out.append(txt)
        except pytesseract.TesseractError:
            continue
    return "\n".join(out)


def _year(y: int) -> int:
    """An din două cifre: 26 -> 2026. Peste 70 devine 19xx."""
    if y > 99:
        return y
    return 2000 + y if y < 70 else 1900 + y


def _safe_date(y: int, m: int, d: int | None) -> date | None:
    if not 1 <= m <= 12:
        return None
    if d is None:
        # Doar luna și anul pe etichetă. Valabil până la finalul lunii.
        d = calendar.monthrange(y, m)[1]
    if not 1 <= d <= calendar.monthrange(y, m)[1]:
        return None
    if not 2000 <= y <= 2100:
        return None
    return date(y, m, d)


# Ordinea contează: tiparele specifice primele, altfel cele largi le fură
# potrivirile.
PATTERNS = [
    # 2026-09-16 sau 2026.09.16
    (r"(20\d{2})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})", lambda g: _safe_date(int(g[0]), int(g[1]), int(g[2]))),
    # 16.09.2026 sau 16/09/26
    (r"(\d{1,2})[.\-/ ](\d{1,2})[.\-/ ](\d{2,4})", lambda g: _safe_date(_year(int(g[2])), int(g[1]), int(g[0]))),
    # 16 SEP 2026
    (r"(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{2,4})", lambda g: _safe_date(_year(int(g[2])), LUNI.get(g[1][:3].lower(), 0), int(g[0]))),
    # SEP 2026
    (r"([A-Za-z]{3,})\s*(20\d{2})", lambda g: _safe_date(int(g[1]), LUNI.get(g[0][:3].lower(), 0), None)),
    # 09.2026 sau 09/26
    (r"(\d{1,2})[.\-/ ](20\d{2})", lambda g: _safe_date(int(g[1]), int(g[0]), None)),
    # 160926, tipărit compact, fără separatori
    (r"\b(\d{2})(\d{2})(\d{2})\b", lambda g: _safe_date(_year(int(g[2])), int(g[1]), int(g[0]))),
]

# Cuvintele care preced de obicei data. Prezența lor ridică încrederea.
HINTS = re.compile(r"exp|valab|best\s*before|use\s*by|consum|termen|scad|bbd|eod", re.I)


def parse_expiry(text: str) -> tuple[date | None, str | None]:
    """Întoarce (data, fragmentul brut din care a ieșit)."""
    cleaned = text.replace("O", "0").replace("o", "0").replace("l", "1")
    candidates = []
    for pattern, builder in PATTERNS:
        for m in re.finditer(pattern, cleaned):
            d = builder(m.groups())
            if d:
                # Contextul: 40 de caractere dinaintea potrivirii.
                context = cleaned[max(0, m.start() - 40):m.start()]
                candidates.append((d, m.group(0), bool(HINTS.search(context))))
    if not candidates:
        return None, None

    # Preferăm una precedată de EXP sau VALABIL. Altfel luăm data cea mai
    # îndepărtată, fiindcă pe ambalaj apare des și data fabricației.
    hinted = [c for c in candidates if c[2]]
    pool = hinted or candidates
    best = max(pool, key=lambda c: c[0])
    return best[0], best[1]


def read_expiry(raw: bytes) -> dict:
    text = extract_text(raw)
    parsed, snippet = parse_expiry(text)
    return {
        "date": parsed.isoformat() if parsed else None,
        "matched": snippet,
        "raw_text": text.strip()[:500],
        "confidence": "high" if parsed and HINTS.search(text) else ("low" if parsed else "none"),
    }
