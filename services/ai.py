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


# ==========================================================================
# TRADUCERE REȚETE
# Site-ul e în engleză, dar oricine poate scrie o rețetă în limba lui. La
# creare/editare detectăm limba și, dacă nu e engleză, salvăm varianta
# tradusă — conținutul din DB rămâne mereu în engleză, iar `source_language`
# spune de unde a venit, ca să putem afișa „Translated from Romanian".
# ==========================================================================

_LANG_NAMES = {
    "en": "English", "ro": "Romanian", "fr": "French", "de": "German",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "nl": "Dutch",
    "pl": "Polish", "hu": "Hungarian", "ru": "Russian", "uk": "Ukrainian",
    "tr": "Turkish", "el": "Greek", "ar": "Arabic", "hi": "Hindi",
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "vi": "Vietnamese",
    "th": "Thai", "sv": "Swedish", "da": "Danish", "no": "Norwegian",
    "fi": "Finnish", "cs": "Czech", "bg": "Bulgarian", "sr": "Serbian",
    "hr": "Croatian", "he": "Hebrew", "id": "Indonesian",
}


def language_name(code: str) -> str:
    """Numele afișabil al unei limbi ('ro' -> 'Romanian')."""
    return _LANG_NAMES.get((code or "").lower(), (code or "").upper())


def translate_recipe(title: str, description: str, ingredients: list, steps: list):
    """Detectează limba rețetei și o traduce în engleză dacă e nevoie.

    Întoarce dict:
      {
        "language": "ro",        # limba sursă detectată (ISO 639-1)
        "translated": bool,      # False = era deja engleză / AI indisponibil
        "title", "description", "ingredients", "steps"   # varianta finală (EN)
      }

    Pe orice eroare întoarce conținutul original, netradus — o rețetă scrisă
    în altă limbă e mai bună decât o rețetă care nu se poate publica.
    """
    original = {
        "language": "en",
        "translated": False,
        "title": title,
        "description": description or "",
        "ingredients": list(ingredients or []),
        "steps": list(steps or []),
    }

    client = _client()
    if client is None:
        return original

    # Trimitem doar textul care chiar se traduce; `timer` rămâne neatins.
    payload = {
        "title": title,
        "description": description or "",
        "ingredients": list(ingredients or []),
        "steps": [
            {
                "text": (s.get("text", "") if isinstance(s, dict) else str(s)),
                "label": (s.get("label", "") if isinstance(s, dict) else ""),
            }
            for s in (steps or [])
        ],
    }

    prompt = f"""You are a culinary translator for an English-language cooking site.

Here is a user-submitted recipe as JSON:
{json.dumps(payload, ensure_ascii=False)}

1. Detect the language the recipe is written in (ISO 639-1 code, e.g. "en", "ro", "fr").
   Judge by the steps and description, not by a dish name.
2. If it is NOT English, translate every text field into natural English, the way a
   cook would write it. Keep quantities, units and numbers exactly as given. Keep
   proper dish names (e.g. "sarmale", "ratatouille") but you may add a short English
   gloss in the title if it helps, e.g. "Sarmale (cabbage rolls)".
3. If it IS already English, return the text unchanged and set "translated": false.

Return STRICT JSON with exactly this shape, with the same number of ingredients and
steps, in the same order:
{{
  "language": "<iso code of the ORIGINAL>",
  "translated": <true|false>,
  "title": "...",
  "description": "...",
  "ingredients": ["...", "..."],
  "steps": [{{"text": "...", "label": "..."}}]
}}
Only output the JSON."""

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(resp.choices[0].message.content)
        lang = str(data.get("language", "en") or "en").lower()[:5]
        translated = bool(data.get("translated")) and lang != "en"
        if not translated:
            return {**original, "language": lang or "en"}

        new_ing = data.get("ingredients") or []
        new_steps = data.get("steps") or []
        # Lungimile trebuie să se potrivească — dacă modelul a sărit sau a
        # inventat linii nu avem cum să le mapăm pe original, deci păstrăm originalul.
        if len(new_ing) != len(payload["ingredients"]) or len(new_steps) != len(payload["steps"]):
            return {**original, "language": lang}

        merged_steps = []
        for src, tr in zip(steps or [], new_steps):
            base = dict(src) if isinstance(src, dict) else {"text": str(src)}
            base["text"] = str(tr.get("text", "") or base.get("text", ""))
            if base.get("label"):
                base["label"] = str(tr.get("label", "") or base["label"])
            merged_steps.append(base)

        return {
            "language": lang,
            "translated": True,
            "title": str(data.get("title") or title),
            "description": str(data.get("description") or description or ""),
            "ingredients": [str(i) for i in new_ing],
            "steps": merged_steps,
        }
    except Exception:
        return original


# ==========================================================================
# COOK-ALONG: întrebări puse în timpul gătitului, cu contextul rețetei
# ==========================================================================

COOK_FALLBACK = (
    "I can't reach my kitchen notes right now. Re-read the current step, give it "
    "a moment, then ask me again."
)


def _recipe_context(recipe: dict, step_index: int) -> str:
    """Blocul de context trimis modelului: rețeta întreagă + unde a ajuns
    utilizatorul. Fără el, AI-ul răspunde generic la „cât mai stă?"."""
    steps = recipe.get("steps") or []
    ingredients = recipe.get("ingredients") or []

    lines = [f"RECIPE: {recipe.get('title', '')}"]
    if recipe.get("origin"):
        lines.append(f"Origin: {recipe['origin']}")
    if recipe.get("description"):
        lines.append(f"Description: {recipe['description']}")

    meta = []
    if recipe.get("servings"):
        meta.append(f"{recipe['servings']} servings")
    if recipe.get("duration_min"):
        meta.append(f"{recipe['duration_min']} min total")
    if recipe.get("calories"):
        meta.append(f"~{recipe['calories']} kcal per serving")
    if meta:
        lines.append("Meta: " + " - ".join(meta))

    lines.append("")
    lines.append("INGREDIENTS:")
    lines.extend(f"- {i}" for i in ingredients)

    lines.append("")
    lines.append("ALL STEPS:")
    for n, s in enumerate(steps):
        text = s.get("text", "") if isinstance(s, dict) else str(s)
        timer = s.get("timer", "") if isinstance(s, dict) else ""
        label = s.get("label", "") if isinstance(s, dict) else ""
        extra = " ".join(
            x for x in [f"[timer: {timer}]" if timer else "", f"[{label}]" if label else ""] if x
        )
        marker = "   <-- THE USER IS HERE" if n == step_index else ""
        lines.append(f"{n + 1}. {text} {extra}{marker}".rstrip())

    current = steps[step_index] if 0 <= step_index < len(steps) else None
    if current is not None:
        ctext = current.get("text", "") if isinstance(current, dict) else str(current)
        lines.append("")
        lines.append(f'CURRENT STEP: step {step_index + 1} of {len(steps)} - "{ctext}"')
    return "\n".join(lines)


COOK_SYSTEM = """You are Kooka, a warm and practical cooking companion talking to
someone who is cooking RIGHT NOW - hands busy, phone propped up on the counter.

Rules:
- You are given the full recipe and exactly which step they are on. Assume every
  question is about that step unless they clearly mean another one.
- Answer in 1-3 short sentences. No lists unless they ask for one, no headings,
  no markdown, no emoji. Plain spoken language.
- Be concrete: temperatures, times, what it should look, smell or sound like.
- If something went wrong, give the rescue first and the explanation second.
- If they ask about a different step, say which step you mean.
- If the recipe genuinely does not say, use standard cooking knowledge and say so
  briefly. Never invent an ingredient that is not in the list.
- Always answer in English."""


def cook_answer(recipe: dict, step_index: int, question: str, history: list = None):
    """Răspunde la o întrebare pusă în timpul gătitului.

    `recipe` e dictul serializat al rețetei (full=True), `step_index` e pasul
    curent (0-based), `history` e lista {role, text} din panoul lateral.
    """
    client = _client()
    if client is None:
        return {"text": COOK_FALLBACK, "ok": False}

    messages = [
        {"role": "system", "content": COOK_SYSTEM},
        {"role": "system", "content": _recipe_context(recipe, step_index)},
    ]
    # ultimele câteva schimburi, ca să poată răspunde la „și acum?"
    for m in (history or [])[-8:]:
        role = "assistant" if m.get("role") == "ai" else "user"
        text = (m.get("text") or "").strip()
        if text:
            messages.append({"role": role, "content": text[:1000]})
    messages.append({"role": "user", "content": question[:1000]})

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        return {"text": text or COOK_FALLBACK, "ok": bool(text)}
    except Exception:
        return {"text": COOK_FALLBACK, "ok": False}
