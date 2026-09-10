"""Alergeni: vocabular canonic + potrivire tolerantă.

Alergenii rețetelor sunt scriși de model în engleză, în text liber („Tree
nuts", „Nuts", „Milk"), iar cei ai utilizatorului sunt bifați dintr-o listă.
Ca cele două să se întâlnească, totul trece prin `canon()`: sinonimele cad pe
aceeași cheie, iar ce nu e recunoscut rămâne ca text normalizat — o alergie
scrisă de mână („mango") tot poate fi filtrată.
"""

# Cele 14 alergene din Regulamentul UE 1169/2011, în ordinea în care le
# arătăm în interfață. `label` e engleza — site-ul e în engleză, la fel ca
# rețetele traduse.
ALLERGENS = [
    {"id": "gluten",      "label": "Gluten",           "emoji": "🌾"},
    {"id": "milk",        "label": "Milk & dairy",     "emoji": "🥛"},
    {"id": "eggs",        "label": "Eggs",             "emoji": "🥚"},
    {"id": "peanuts",     "label": "Peanuts",          "emoji": "🥜"},
    {"id": "nuts",        "label": "Tree nuts",        "emoji": "🌰"},
    {"id": "soy",         "label": "Soy",              "emoji": "🫘"},
    {"id": "fish",        "label": "Fish",             "emoji": "🐟"},
    {"id": "crustaceans", "label": "Crustaceans",      "emoji": "🦐"},
    {"id": "molluscs",    "label": "Molluscs",         "emoji": "🦪"},
    {"id": "sesame",      "label": "Sesame",           "emoji": "🫓"},
    {"id": "celery",      "label": "Celery",           "emoji": "🥬"},
    {"id": "mustard",     "label": "Mustard",          "emoji": "🌭"},
    {"id": "lupin",       "label": "Lupin",            "emoji": "🌱"},
    {"id": "sulphites",   "label": "Sulphites",        "emoji": "🍷"},
]

ALLERGEN_IDS = [a["id"] for a in ALLERGENS]
ALLERGEN_BY_ID = {a["id"]: a for a in ALLERGENS}

# Cum poate să scrie modelul (sau utilizatorul) fiecare alergen.
_SYNONYMS = {
    "gluten": ("gluten", "wheat", "cereals containing gluten", "barley", "rye",
               "spelt", "flour", "bread"),
    "milk": ("milk", "dairy", "lactose", "cheese", "butter", "cream", "yoghurt",
             "yogurt"),
    "eggs": ("egg", "eggs"),
    "peanuts": ("peanut", "peanuts", "groundnut", "groundnuts"),
    "nuts": ("nut", "nuts", "tree nut", "tree nuts", "almond", "almonds",
             "hazelnut", "hazelnuts", "walnut", "walnuts", "cashew", "cashews",
             "pistachio", "pistachios", "pecan", "pecans", "macadamia"),
    "soy": ("soy", "soya", "soybean", "soybeans", "soia", "tofu"),
    "fish": ("fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "sardine",
             "sardines"),
    "crustaceans": ("crustacean", "crustaceans", "shellfish", "shrimp",
                    "prawn", "prawns", "crab", "lobster"),
    "molluscs": ("mollusc", "molluscs", "mollusk", "mollusks", "squid",
                 "octopus", "mussel", "mussels", "clam", "clams", "oyster",
                 "oysters", "snail", "snails"),
    "sesame": ("sesame", "tahini"),
    "celery": ("celery", "celeriac"),
    "mustard": ("mustard",),
    "lupin": ("lupin", "lupine"),
    "sulphites": ("sulphite", "sulphites", "sulfite", "sulfites",
                  "sulphur dioxide", "sulfur dioxide"),
}

_LOOKUP = {}
for _id, _words in _SYNONYMS.items():
    for _w in _words:
        _LOOKUP[_w] = _id


def canon(value: str) -> str:
    """Cheia canonică pentru un alergen scris oricum. Ce nu e în vocabular se
    întoarce normalizat (lowercase, fără spații în plus), nu aruncat."""
    text = (value or "").strip().lower()
    if not text:
        return ""
    if text in _LOOKUP:
        return _LOOKUP[text]
    # potrivire pe substring: „contains milk", „tree nuts (almonds)"
    for word, key in _LOOKUP.items():
        if word in text:
            return key
    return text


def parse_user(raw: str) -> list:
    """`User.allergies` e o listă simplă separată prin virgulă."""
    if not raw:
        return []
    out = []
    for part in str(raw).split(","):
        key = canon(part)
        if key and key not in out:
            out.append(key)
    return out


def serialize_user(values) -> str:
    """Invers: din lista bifată în interfață înapoi în coloană."""
    seen = []
    for v in values or []:
        key = canon(v)
        if key and key not in seen:
            seen.append(key)
    return ",".join(seen)


def recipe_keys(allergens: dict) -> set:
    """Cheile canonice pe care le CONȚINE o rețetă."""
    contains = (allergens or {}).get("contains") or []
    return {canon(a) for a in contains if canon(a)}


def conflicts(user_keys, allergens: dict) -> list:
    """Intersecția — ce anume din rețetă lovește alergiile declarate."""
    if not user_keys:
        return []
    return sorted(recipe_keys(allergens) & set(user_keys))


def label_of(key: str) -> str:
    meta = ALLERGEN_BY_ID.get(key)
    return meta["label"] if meta else key.title()


def table() -> list:
    """Lista trimisă frontend-ului pentru ecranele de bifat."""
    return [dict(a) for a in ALLERGENS]
