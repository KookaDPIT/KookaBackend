"""Integrare Groq: estimare nutriție, moderare rețete și verificare vizuală
că poza de gătit e mâncare plauzibilă.

Toate funcțiile sunt tolerante la erori: dacă Groq nu răspunde sau cheia
lipsește, întorc un fallback grațios ca să nu blocheze crearea rețetei."""
import os
import json

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Nutriție implicită (per porție) când AI-ul nu răspunde — structura pe care o
# așteaptă frontendul pentru gauge-uri.
_EMPTY_NUTRITION = [
    {"key": "kcal", "label": "Calories", "value": 0, "unit": "kcal", "max": 2000},
    {"key": "prot", "label": "Protein", "value": 0, "unit": "g", "max": 50},
    {"key": "fat", "label": "Fat", "value": 0, "unit": "g", "max": 70},
    {"key": "carb", "label": "Carbs", "value": 0, "unit": "g", "max": 260},
    {"key": "salt", "label": "Salt", "value": 0, "unit": "g", "max": 6},
]


def _client():
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


def analyze_recipe(title: str, ingredients: list, steps: list, servings: int = 1):
    """Estimează nutriția + alergenii și validează că rețeta e reală.

    Întoarce dict:
      {
        "valid": bool,          # False = spam / prostii
        "reason": str,          # explicație scurtă dacă invalid
        "calories": int,        # kcal per porție
        "nutrition": [...],     # structura de gauge-uri
        "allergens": {"contains": [...], "free": [...]},
      }
    """
    fallback = {
        "valid": True,
        "reason": "",
        "calories": 0,
        "nutrition": _EMPTY_NUTRITION,
        "allergens": {"contains": [], "free": []},
    }

    client = _client()
    if client is None:
        return fallback

    step_texts = [s.get("text", "") if isinstance(s, dict) else str(s) for s in steps]
    prompt = f"""You are a culinary and nutrition expert. Analyze this user-submitted recipe.

Title: {title}
Servings: {servings}
Ingredients:
{chr(10).join('- ' + i for i in ingredients)}
Steps:
{chr(10).join(f'{n+1}. ' + s for n, s in enumerate(step_texts))}

Do two things:
1. Decide if this is a genuine food recipe. Set "valid": false ONLY for clear abuse —
   spam, gibberish/random characters, offensive content, or non-food / dangerous
   (non-edible) instructions. Do NOT reject a real recipe just because it is short,
   incomplete, missing some ingredients, or imperfectly written — those are still
   "valid": true. Give a short "reason" only when you set valid=false.
2. Estimate nutrition PER SERVING and detect allergens.

Return STRICT JSON with exactly this shape:
{{
  "valid": true,
  "reason": "",
  "calories": <int kcal per serving>,
  "nutrition": [
    {{"key":"kcal","label":"Calories","value":<int>,"unit":"kcal","max":2000}},
    {{"key":"prot","label":"Protein","value":<int>,"unit":"g","max":50}},
    {{"key":"fat","label":"Fat","value":<int>,"unit":"g","max":70}},
    {{"key":"carb","label":"Carbs","value":<int>,"unit":"g","max":260}},
    {{"key":"salt","label":"Salt","value":<number>,"unit":"g","max":6}}
  ],
  "allergens": {{"contains": ["Gluten","Eggs"], "free": ["Nuts","Fish"]}}
}}
Only output the JSON."""

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
        # normalizare defensivă
        return {
            "valid": bool(data.get("valid", True)),
            "reason": str(data.get("reason", "")),
            "calories": int(data.get("calories", 0) or 0),
            "nutrition": data.get("nutrition") or _EMPTY_NUTRITION,
            "allergens": data.get("allergens") or {"contains": [], "free": []},
        }
    except Exception:
        return fallback


def verify_cook(title: str, image_url: str):
    """Verifică (permisiv) că poza e mâncare gătită plauzibilă.

    Întoarce {"verified": bool, "reason": str}. Dacă Groq nu e disponibil,
    acceptă (verified=True) ca să nu blocheze utilizatorul."""
    client = _client()
    if client is None or not image_url:
        return {"verified": True, "reason": "verificare indisponibilă, acceptat implicit"}

    prompt = (
        f"Look at this photo. The user claims they cooked the dish '{title}'. "
        "Be permissive: your only job is to confirm the photo shows real, prepared "
        "food/a cooked dish (not a screenshot, a random object, a person, or an empty "
        "plate). It does NOT need to exactly match the named dish. "
        'Return STRICT JSON: {"is_food": bool, "plausible": bool, "confidence": 0..1, "reason": "short"}'
    )
    try:
        resp = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(resp.choices[0].message.content)
        verified = bool(data.get("is_food")) and bool(data.get("plausible"))
        return {"verified": verified, "reason": str(data.get("reason", ""))}
    except Exception:
        # eroare de model -> acceptăm ca să nu blocăm fluxul
        return {"verified": True, "reason": "verificare eșuată tehnic, acceptat implicit"}
