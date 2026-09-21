"""Integrare Groq: estimare nutriție, moderare rețete și verificare vizuală
că poza de gătit e mâncare plauzibilă.

Toate funcțiile sunt tolerante la erori: dacă Groq nu răspunde sau cheia
lipsește, întorc un fallback grațios ca să nu blocheze crearea rețetei."""
import os
import json

from dotenv import load_dotenv

from services import courses

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
# Munca de fundal (traducere, nutriție, moderare) — treabă tăcută, la care nimeni
# nu se uită cum scrie. Groq numără tokenii SEPARAT pentru fiecare model, așa că
# mutând-o pe alt model îi dai conversației cu utilizatorul o cotă întreagă doar
# a ei. Implicit rămâne pe TEXT_MODEL: setează GROQ_UTILITY_MODEL ca să separi.
UTILITY_MODEL = os.getenv("GROQ_UTILITY_MODEL", "") or TEXT_MODEL

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
        "course": str,          # tipul felului (services/courses.COURSE_IDS)
      }
    """
    # `ok` says whether these numbers came from the model or are the empty
    # shape we fall back to when Groq is unreachable. Publishing tolerates the
    # empty shape — better a recipe with no nutrition than no recipe — but
    # anything that OVERWRITES existing data must check it first, or a moderator
    # pressing "re-analyse" while the key is missing would wipe good values.
    fallback = {
        "ok": False,
        "valid": True,
        "reason": "",
        "calories": 0,
        "nutrition": _EMPTY_NUTRITION,
        "allergens": {"contains": [], "free": []},
        "course": "",
    }

    client = _client()
    if client is None:
        return fallback

    step_texts = [s.get("text", "") if isinstance(s, dict) else str(s) for s in steps]
    # Interpolat direct în f-string, nu printr-un `.replace` de după: un
    # `{PLACEHOLDER}` scris într-un f-string e evaluat ca expresie la
    # construirea șirului, deci pică pe NameError înainte ca `.replace` să apuce
    # să ruleze. Asta a scos din funcțiune și publicarea, și editarea rețetelor.
    course_list = ", ".join(courses.COURSE_IDS)
    prompt = f"""You are a culinary and nutrition expert. Analyze this user-submitted recipe.

Title: {title}
Servings: {servings}
Ingredients:
{chr(10).join('- ' + i for i in ingredients)}
Steps:
{chr(10).join(f'{n+1}. ' + s for n, s in enumerate(step_texts))}

Do three things:
1. Decide if this is a genuine food recipe. Set "valid": false ONLY for clear abuse —
   spam, gibberish/random characters, offensive content, or non-food / dangerous
   (non-edible) instructions. Do NOT reject a real recipe just because it is short,
   incomplete, missing some ingredients, or imperfectly written — those are still
   "valid": true. Give a short "reason" only when you set valid=false.
2. Estimate nutrition PER SERVING and detect allergens.
3. Classify what KIND of dish this is, choosing exactly one id from this closed
   list: {course_list}. Pick the one a diner would use, not the one the
   ingredients suggest: a chocolate cake is "dessert", not "bakery". Use "main"
   when nothing else fits.

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
  "allergens": {{"contains": ["Gluten","Eggs"], "free": ["Nuts","Fish"]}},
  "course": "dessert"
}}
Only output the JSON."""

    try:
        resp = client.chat.completions.create(
            model=UTILITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
        # normalizare defensivă
        return {
            "ok": True,
            "valid": bool(data.get("valid", True)),
            "reason": str(data.get("reason", "")),
            "calories": int(data.get("calories", 0) or 0),
            "nutrition": data.get("nutrition") or _EMPTY_NUTRITION,
            "allergens": data.get("allergens") or {"contains": [], "free": []},
            # Un id inventat de model e la fel de inutil ca unul lipsă: cădem
            # pe euristica din titlu, care măcar respectă vocabularul.
            "course": courses.normalize(data.get("course", ""))
            or courses.guess(title, ingredients),
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


def _ui_language_line(code: str) -> str:
    """Linia de sistem care spune modelului pe ce limbă să cadă înapoi.

    Limba răspunsului o decide mesajul omului — el poate scrie în franceză cu
    interfața pe engleză. Asta e doar plasa pentru „ok", „și acum?", „merci",
    mesaje prea scurte ca să aibă o limbă.
    """
    code = (code or "en").lower()[:2]
    return (
        f"The interface this person is using is set to {language_name(code)} "
        f"({code}). Reply in the language of THEIR MESSAGE; fall back to "
        f"{language_name(code)} only when the message is too short to tell."
    )


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
            model=UTILITY_MODEL,
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


def translate_into(
    title: str,
    description: str,
    ingredients: list,
    steps: list,
    target: str,
):
    """Traduce o rețetă ÎN limba cerută, la cerere.

    Sora lui `translate_recipe`, dar în sens invers și pe alt declanșator: aia
    rulează tăcut la publicare și scoate mereu engleză (ce se caută și ce
    citește AI-ul), asta rulează doar când cineva apasă „tradu" și scoate limba
    lui. Nimic din ce iese de aici nu înlocuiește textul rețetei în DB — se
    salvează separat, ca o traducere, ca să n-o mai plătim a doua oară.

    Întoarce {"ok", "language", "title", "description", "ingredients", "steps"};
    `ok=False` înseamnă că nu s-a tradus nimic (AI indisponibil sau răspuns
    inutilizabil) și apelantul trebuie să arate textul original.
    """
    code = (target or "").lower()[:2]
    failed = {
        "ok": False,
        "language": code,
        "title": title,
        "description": description or "",
        "ingredients": list(ingredients or []),
        "steps": list(steps or []),
    }
    if not code:
        return failed

    client = _client()
    if client is None:
        return failed

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
    target_name = language_name(code)

    prompt = f"""You are a culinary translator. Translate this recipe into {target_name} ({code}).

Recipe as JSON:
{json.dumps(payload, ensure_ascii=False)}

Rules:
- Translate every text field into natural {target_name}, the way a cook in that
  language would write it - not word for word.
- Keep every quantity, unit and number exactly as given. Do not convert units.
- Keep proper dish names (e.g. "ratatouille", "sarmale") in their own form.
- Return the SAME number of ingredients and steps, in the SAME order.
- If a field is already in {target_name}, return it unchanged.

Return STRICT JSON with exactly this shape:
{{
  "title": "...",
  "description": "...",
  "ingredients": ["...", "..."],
  "steps": [{{"text": "...", "label": "..."}}]
}}
Only output the JSON."""

    try:
        resp = client.chat.completions.create(
            model=UTILITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
        new_ing = data.get("ingredients") or []
        new_steps = data.get("steps") or []
        # Aceeași verificare ca la traducerea spre engleză: dacă modelul a sărit
        # sau a inventat linii nu le putem mapa peste original, iar o listă de
        # ingrediente decalată față de pași e mai rea decât textul netradus.
        if len(new_ing) != len(payload["ingredients"]) or len(new_steps) != len(payload["steps"]):
            return failed

        merged_steps = []
        for src, tr in zip(steps or [], new_steps):
            base = dict(src) if isinstance(src, dict) else {"text": str(src)}
            base["text"] = str(tr.get("text", "") or base.get("text", ""))
            if base.get("label"):
                base["label"] = str(tr.get("label", "") or base["label"])
            merged_steps.append(base)

        return {
            "ok": True,
            "language": code,
            "title": str(data.get("title") or title),
            "description": str(data.get("description") or description or ""),
            "ingredients": [str(i) for i in new_ing],
            "steps": merged_steps,
        }
    except Exception:
        return failed


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
- LANGUAGE: reply in the SAME language the person wrote their question in. Work
  it out from their message, not from the recipe - the recipe text is always
  stored in English, so it tells you nothing about what they speak. If their
  message is too short to tell ("ok", "si acum?"), use the interface language
  given below. Never switch language mid-conversation unless they do."""


def cook_answer(
    recipe: dict,
    step_index: int,
    question: str,
    history: list = None,
    ui_language: str = "en",
):
    """Răspunde la o întrebare pusă în timpul gătitului.

    `recipe` e dictul serializat al rețetei (full=True), `step_index` e pasul
    curent (0-based), `history` e lista {role, text} din panoul lateral.
    `ui_language` e limba interfeței — folosită doar ca plasă când întrebarea
    e prea scurtă ca să-i ghicești limba.
    """
    client = _client()
    if client is None:
        return {"text": COOK_FALLBACK, "ok": False}

    messages = [
        {"role": "system", "content": COOK_SYSTEM},
        {"role": "system", "content": _ui_language_line(ui_language)},
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


# ==========================================================================
# CHAT LIBER CU KOOKA
# Spre deosebire de cook-along (unde contextul e o singură rețetă), aici
# modelul primește catalogul de rețete la care userul chiar are acces și
# poate să recomande din el. Ce iese e text de conversație plus, opțional,
# atașamente structurate: rețete reale (carduri) și o estimare nutrițională.
# ==========================================================================

CHAT_FALLBACK = (
    "I'm having trouble reaching my recipe books right now. Give me a moment "
    "and ask me again."
)

CHAT_SYSTEM = """You are Kooka, the cooking companion built into the Kooka app.
You are talking to a home cook. Be warm, direct and practical - like a friend who
happens to cook well, not like a manual.

How to talk:
- Plain conversational English. Short paragraphs. Answer the question first.
- Use a "- " bullet list only when you are genuinely listing things (options,
  ingredients, steps). Never more than 6 bullets. No headings, no tables, no emoji.
- You may use **bold** sparingly for an ingredient or a number that matters.
- Ask a follow-up question when you genuinely need one thing to answer well.
  Otherwise just answer - do not interrogate people.
- Cooking is your subject. If someone asks about something else, answer briefly
  and steer back to food without being preachy.

Recommending recipes:
- The CATALOGUE below is what this app actually has for this user. It is already
  filtered to their question and de-duplicated, so each line is a distinct dish.
- ALWAYS check the catalogue before you answer. If something in it fits, that is
  what you recommend: put the ids in "recipe_ids" (at most 3, best first) and
  talk about THOSE recipes by name in your text - their real time, calories and
  rating, exactly as listed. Do not describe a different version from memory
  while showing a card for ours; the person sees the card next to your words.
- When two entries are close, prefer the better-rated one, then the faster one.
- Only ever use ids from the catalogue. Never invent an id and never claim the
  app has a recipe it does not.
- Ids are plumbing: they belong in "recipe_ids" only. NEVER write an id in your
  reply text ("recipe 2", "id 3"). The person sees a card with the recipe's name
  on it, not a number - so refer to it by name, e.g. "I've put our Spaghetti
  carbonara below".
- If nothing in the catalogue fits, say so plainly - "we don't have one for that
  yet" - and then help from your own cooking knowledge, with "recipe_ids": [].
  Do not pad the list with recipes that only vaguely relate.
- A PHOTO OF INGREDIENTS (a fridge, a counter, a shopping bag) is a question
  about the catalogue even when no words came with it. Say what you see, then
  recommend the catalogue dishes those ingredients would make - the ingredients
  we read out of the photo are listed for you below. Suggesting dishes from
  memory while our own recipes for them sit unmentioned is the one thing this
  answer must not do. Only if nothing in the catalogue can be made with what is
  there do you fall back to your own ideas, and then you say so.

Estimating what someone ate:
- If they describe food they have eaten and want to know the calories, fill in
  "nutrition" with your best estimate. Otherwise leave it null.

The shopping list and the meal plan:
- This person has a real shopping list and a real weekly meal calendar in the
  app, and you can write to both. Their current contents are shown to you below
  when they have any - never add something that is already on the list.
- When they ask you to add ingredients ("put eggs and milk on my list", "add
  what I need for that"), put them in "plan.shopping_add". One entry per
  ingredient, with the amount split out: {"name": "flour", "quantity": "200",
  "unit": "g"}. Leave quantity and unit empty when there is no sensible amount.
- When they ask you to plan meals ("plan my weekend", "put that on Friday",
  "give me a week of dinners"), put them in "plan.meals". Use real dates in
  YYYY-MM-DD - today's date is given below, so work them out yourself. Use
  "recipe_id" when the dish is one from the catalogue, and "title" when it is
  not; a slot is one of breakfast, lunch, dinner, snack.
- Only fill "plan" when they actually asked you to change something. Answering
  "what should I cook this weekend?" is a conversation; "plan my weekend" is an
  instruction. When in doubt, suggest in your text and leave "plan" empty.
- After you fill "plan", say plainly what you added in your reply - the person
  sees a summary card, but the words are what they read first.

Language:
- Write "reply" in the SAME language the person just wrote to you in. Detect it
  from their message; when it is too short to tell, use the interface language
  given below. Titles you generate follow the same language as the reply.
- The catalogue is stored in English. Keep recipe names exactly as they appear
  there even when you are writing in another language - that is the name on the
  card next to your words - but write everything around them in their language.
- Ingredient names inside "plan.shopping_add" also go in their language: that
  list is read in a shop, by them."""


def see_ingredients(image_data_uri: str) -> list:
    """Ce alimente se văd în poză, ca listă de cuvinte în engleză.

    O trecere separată, înaintea răspunsului propriu-zis, fiindcă altfel
    catalogul de rețete se alege în orb: cel care alege ce rețete îi arătăm
    modelului se uită la TEXTUL mesajului, iar la o poză de frigider textul e
    gol. Rezultatul nu ajunge la om — e doar cheia după care sortăm catalogul,
    și de-aia e în engleză, ca titlurile rețetelor din DB.

    Pe orice eroare întoarce o listă goală: fără ea chatul răspunde exact ca
    înainte, doar fără recomandări din aplicație.
    """
    client = _client()
    if client is None or not image_data_uri:
        return []

    prompt = (
        "List the food ingredients you can see in this photo. Only things that "
        "can be cooked or eaten. Use plain English singular nouns, no amounts, "
        "no adjectives, at most 20 of them. If you see no food, return an empty "
        'list. Return STRICT JSON: {"ingredients": ["egg", "carrot", "spinach"]}'
    )
    try:
        resp = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_uri}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=250,
        )
        data = json.loads(resp.choices[0].message.content)
        items = data.get("ingredients") or []
        return [str(i).strip().lower() for i in items[:20] if str(i).strip()]
    except Exception:
        return []


def _chat_json_shape(want_title: bool) -> str:
    title_line = (
        '  "title": "<3-6 word name for this conversation>",\n' if want_title else ""
    )
    return f"""Return STRICT JSON with exactly this shape:
{{
{title_line}  "reply": "<your answer, plain text>",
  "recipe_ids": [<ids from the catalogue, or empty>],
  "nutrition": null,
  "plan": null
}}
When you are estimating a meal, "nutrition" instead looks like:
{{
  "total_kcal": <int>, "confidence": "low|medium|high",
  "items": [{{"name": "...", "detail": "2 slices", "kcal": <int>}}],
  "macros": {{"carbs_g": <int>, "fat_g": <int>, "protein_g": <int>}}
}}
When they asked you to change their shopping list or meal plan, "plan" instead
looks like (either key may be an empty list):
{{
  "shopping_add": [{{"name": "flour", "quantity": "200", "unit": "g"}}],
  "meals": [{{"date": "2026-09-19", "slot": "dinner",
             "recipe_id": <id from the catalogue, or omit>,
             "title": "<dish name when it is not one of ours>"}}]
}}
Only output the JSON."""


def chat_reply(
    message: str,
    history: list = None,
    user_ctx: dict = None,
    catalogue: list = None,
    image_data_uri: str = None,
    want_title: bool = False,
    planner_lines: list = None,
    ui_language: str = "en",
    seen_ingredients: list = None,
):
    """Un tur de conversație cu Kooka.

    `catalogue` e o listă de dict-uri {id, title, origin, duration_min, calories,
    rank, avg, reviews} — doar rețete la care userul are acces, deja
    deduplicate. `image_data_uri` mută apelul pe modelul de vision (poza nu se
    stochează nicăieri).

    Întoarce {"text", "recipe_ids", "nutrition", "title", "ok"}.
    """
    empty = {
        "text": CHAT_FALLBACK,
        "recipe_ids": [],
        "nutrition": None,
        "plan": None,
        "title": "",
        "ok": False,
    }

    client = _client()
    if client is None:
        return empty

    context_lines = [_ui_language_line(ui_language), ""]
    if user_ctx:
        who = user_ctx.get("name") or "this cook"
        context_lines.append(f"You are talking to {who}.")
        if user_ctx.get("rank"):
            context_lines.append(
                f"Their rank in the app is {user_ctx['rank']} - keep suggestions "
                "at or below that level of difficulty."
            )

    if seen_ingredients:
        context_lines.append("")
        context_lines.append(
            "IN THE PHOTO - what we read out of the picture they just sent: "
            + ", ".join(seen_ingredients)
            + ". The catalogue below was chosen to match these, so look there "
            "first for something they can cook tonight."
        )

    if planner_lines:
        context_lines.append("")
        context_lines.extend(planner_lines)

    if catalogue:
        context_lines.append("")
        context_lines.append(
            "CATALOGUE - the recipes this app actually has for this user. "
            "Rating is shown as average/number of reviews."
        )
        context_lines.append("id | title | origin | time | kcal | rank | rating")
        for r in catalogue:
            reviews = r.get("reviews") or 0
            rating = f"{r.get('avg', 0):.1f}/{reviews}" if reviews else "unrated"
            context_lines.append(
                f"{r['id']} | {r['title']} | {r.get('origin') or '-'} | "
                f"{r.get('duration_min') or '?'} min | {r.get('calories') or '?'} kcal | "
                f"{r.get('rank') or '-'} | {rating}"
            )
    else:
        context_lines.append("")
        context_lines.append(
            "CATALOGUE: empty - this app has no recipes you can point them to yet, "
            'so always return "recipe_ids": [].'
        )

    messages = [
        {"role": "system", "content": CHAT_SYSTEM},
        {"role": "system", "content": "\n".join(context_lines)},
        {"role": "system", "content": _chat_json_shape(want_title)},
    ]

    for m in (history or [])[-12:]:
        role = "assistant" if m.get("role") == "ai" else "user"
        text = (m.get("text") or "").strip()
        if text:
            messages.append({"role": role, "content": text[:2000]})

    if image_data_uri:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message[:2000] or "What do you see here?"},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                ],
            }
        )
    else:
        messages.append({"role": "user", "content": message[:2000]})

    try:
        resp = client.chat.completions.create(
            model=VISION_MODEL if image_data_uri else TEXT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.6,
            max_tokens=1200,
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception:
        return empty

    # ids valide = doar cele chiar existente în catalog; modelul mai inventează
    allowed = {int(r["id"]) for r in (catalogue or [])}
    ids = []
    for rid in (data.get("recipe_ids") or [])[:3]:
        try:
            rid = int(rid)
        except (TypeError, ValueError):
            continue
        if rid in allowed and rid not in ids:
            ids.append(rid)

    text = str(data.get("reply") or "").strip()
    # `plan` is a request to write to the person's list and calendar. It is
    # passed straight through — every field is re-checked in services/planner.py
    # before anything is stored, so a hallucinated recipe id or a date in 2019
    # cannot reach the database from here.
    plan = data.get("plan") if isinstance(data.get("plan"), dict) else None
    return {
        "text": text or CHAT_FALLBACK,
        "recipe_ids": ids,
        "nutrition": data.get("nutrition") if isinstance(data.get("nutrition"), dict) else None,
        "plan": plan,
        "title": str(data.get("title") or "").strip()[:80],
        "ok": bool(text),
    }
