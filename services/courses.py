# -*- coding: utf-8 -*-
"""Tipul felului de mâncare — „ce e asta", nu „din ce e făcută".

Căutarea avea doar titlu și țară, deci „vreau un desert" nu era o întrebare pe
care o puteai pune. Asta e vocabularul fix care o face posibilă, și tot el dă
tag-ul de mic dejun de care au nevoie trofeele.

Vocabularul e **închis** intenționat. Tag-uri libere ar însemna „dessert",
„desert", „Desserts" și „sweet" ca patru categorii diferite, iar un filtru cu
patru butoane pentru același lucru nu e un filtru. Cine scrie o rețetă alege
dintr-o listă; analizorul AI alege tot din ea; rețetele vechi sunt clasificate
o dată, euristic, de funcția de mai jos.

`meals` spune la ce mese se potrivește fiecare tip. Nu e o a doua coloană în
DB — se deduce din curs — pentru că a întreba autorul și „ce fel e" și „la ce
masă se mănâncă" ar fi două întrebări pentru aceeași informație.
"""
import re

COURSES = [
    {"id": "breakfast",  "name": "Breakfast",  "meals": ["breakfast"]},
    {"id": "appetizer",  "name": "Appetizer",  "meals": ["lunch", "dinner"]},
    {"id": "soup",       "name": "Soup",       "meals": ["lunch", "dinner"]},
    {"id": "salad",      "name": "Salad",      "meals": ["lunch", "dinner"]},
    {"id": "main",       "name": "Main course", "meals": ["lunch", "dinner"]},
    {"id": "side",       "name": "Side dish",  "meals": ["lunch", "dinner"]},
    {"id": "dessert",    "name": "Dessert",    "meals": ["lunch", "dinner"]},
    {"id": "bakery",     "name": "Bread & bakery", "meals": ["breakfast", "snack"]},
    {"id": "snack",      "name": "Snack",      "meals": ["snack"]},
    {"id": "drink",      "name": "Drink",      "meals": ["breakfast", "snack"]},
]

COURSE_IDS = [c["id"] for c in COURSES]
COURSE_BY_ID = {c["id"]: c for c in COURSES}

# Cele trei mese, pentru filtrul „ce pot mânca la prânz" și pentru trofee.
MEALS = ["breakfast", "lunch", "dinner", "snack"]

DEFAULT_COURSE = "main"


def normalize(value: str) -> str:
    """Un curs valid, altfel șirul gol.

    Gol ≠ „main": o rețetă neclasificată trebuie să poată fi găsită de sweep-ul
    de backfill, iar dacă o forțăm pe „main" la citire n-o mai găsește nimeni.
    """
    value = (value or "").strip().lower()
    return value if value in COURSE_BY_ID else ""


def meals_for(course: str) -> list:
    return COURSE_BY_ID.get(normalize(course), {}).get("meals", [])


def courses_for_meal(meal: str) -> list:
    """Ce tipuri de fel se potrivesc la o masă — invers față de `meals_for`."""
    meal = (meal or "").strip().lower()
    return [c["id"] for c in COURSES if meal in c["meals"]]


# ---------- clasificarea euristică a rețetelor vechi ----------
#
# Rulează o singură dată, la migrare, ca sute de rețete existente să nu apară
# drept „neclasificate" în ziua în care apare filtrul. Analizorul AI e mai bun
# și le rescrie la următorul sweep — asta e doar ca filtrul să nu pornească gol.
#
# Conținutul din DB e în engleză (routers/recipes traduce la publicare), dar
# rețetele de dinaintea traducerii au rămas în original, deci lista include și
# cuvinte românești.
_KEYWORDS = [
    ("soup", ["soup", "broth", "chowder", "bisque", "ciorba", "ciorbă", "supa", "supă", "bors", "borș"]),
    ("dessert", [
        "cake", "tart", "pie", "tiramisu", "mousse", "pudding", "ice cream", "brownie",
        "cheesecake", "cookie", "biscuit", "custard", "compote", "trifle", "sorbet",
        "prajitur", "prăjitur", "tort", "desert", "budinca", "budincă", "inghetat", "înghețat",
        "clatite", "clătite", "papanas", "papanaș", "gogos", "gogoș",
    ]),
    ("salad", ["salad", "salata", "salată", "slaw", "coleslaw"]),
    ("breakfast", [
        "breakfast", "omelette", "omelet", "pancake", "porridge", "oatmeal", "granola",
        "scrambled egg", "mic dejun", "omleta", "omletă", "terci",
    ]),
    ("bakery", [
        "bread", "focaccia", "brioche", "bagel", "croissant", "baguette", "sourdough",
        "muffin", "scone", "paine", "pâine", "cozonac", "placinta", "plăcintă", "covrig",
    ]),
    ("drink", [
        "smoothie", "juice", "cocktail", "lemonade", "tea", "coffee", "latte", "milkshake",
        "limonad", "suc de", "ceai", "cafea",
    ]),
    ("appetizer", [
        "appetizer", "starter", "dip", "bruschetta", "hummus", "tapas", "canape", "crostini",
        "aperitiv", "gustare rece", "pate", "pateu",
    ]),
    ("snack", ["snack", "popcorn", "chips", "energy ball", "gustare"]),
    ("side", [
        "side dish", "mashed potato", "fries", "rice pilaf", "garnitura", "garnitură",
        "piure", "cartofi prajiti", "cartofi prăjiți",
    ]),
]


def guess(title: str, ingredients=None, description: str = "") -> str:
    """Ghicește cursul dintr-un titlu (plus descriere/ingrediente ca sprijin).

    Ordinea din `_KEYWORDS` contează: „soup" înainte de „salad" pentru că
    „ciorbă de salată verde" e o ciorbă. Nimic potrivit → felul principal, care
    e categoria cea mai largă și cea mai puțin greșită ca implicit.
    """
    haystack = " ".join([
        (title or ""),
        (description or ""),
        " ".join(str(i) for i in (ingredients or [])),
    ]).lower()
    # Titlul cântărește mai mult: „chocolate cake" cu făină în ingrediente e
    # tot desert, nu produs de panificație.
    title_only = (title or "").lower()

    for course, words in _KEYWORDS:
        if any(w in title_only for w in words):
            return course
    for course, words in _KEYWORDS:
        if any(re.search(r"\b" + re.escape(w), haystack) for w in words):
            return course
    return DEFAULT_COURSE


def table() -> list:
    """Vocabularul complet, trimis frontend-ului o singură dată."""
    return [dict(c) for c in COURSES]


# ---------- filtrul comun listei și căutării ----------

def apply_facets(query, recipe_model, course: str, meal: str,
                 kcal_min: int = 0, kcal_max: int = 0):
    """Filtrele „ce fel de mâncare" și „câte calorii".

    Stă aici, nu în routerul de rețete, pentru că îl folosesc și /recipes, și
    /search — iar un router care importă alt router ca să ajungă la o funcție
    cu underscore e o dependență pe care nimeni n-o caută.

    `course` acceptă mai multe valori separate prin virgulă (sunt bife, nu un
    radio: „desert sau gustare" e o întrebare rezonabilă). `meal` e traducerea
    lui în tipuri de fel — „ce pot mânca la micul dejun" înseamnă ceva pentru
    utilizator și nimic pentru DB.

    Plafonul de calorii ignoră rețetele cu 0 kcal: zero nu e „foarte ușoară", e
    „încă neanalizată", iar un filtru „sub 400 kcal" plin de rețete fără date ar
    fi mai rău decât unul mai scurt. Pragul minim le exclude oricum.
    """
    wanted = [c for c in (normalize(x) for x in (course or "").split(",")) if c]
    if meal:
        from_meal = courses_for_meal(meal)
        wanted = [c for c in wanted if c in from_meal] if wanted else from_meal
        if not wanted:
            # masă necunoscută: mai bine niciun rezultat decât toate
            wanted = ["__none__"]
    if wanted:
        query = query.filter(recipe_model.course.in_(wanted))

    if kcal_min:
        query = query.filter(recipe_model.calories >= kcal_min)
    if kcal_max:
        query = query.filter(
            recipe_model.calories <= kcal_max,
            recipe_model.calories > 0,
        )
    return query
