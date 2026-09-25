# -*- coding: utf-8 -*-
"""Tipul felului de mâncare: „ce e asta", nu „din ce e făcută".

Căutarea avea doar titlu și țară, deci „vreau un desert" nu era o întrebare pe
care o puteai pune. Aici e vocabularul fix care o face posibilă, și tot el dă
tag-ul de mic dejun cerut de trofee.

Vocabularul e închis, intenționat. Tag-uri libere ar însemna „dessert",
„desert", „Desserts" și „sweet" ca patru categorii, iar un filtru cu patru
butoane pentru același lucru nu e un filtru. Autorul alege dintr-o listă,
analizorul AI alege din aceeași listă, iar rețetele vechi sunt clasificate o
dată, euristic, de guess() mai jos.

`meals` spune la ce mese se potrivește fiecare tip. Se deduce din curs, nu e a
doua coloană în DB: altfel l-am întreba pe autor și „ce fel e", și „la ce masă
se mănâncă", adică aceeași informație de două ori.

Ordinea din fișier: vocabularul, normalize(), clasificarea euristică, și
filtrul comun folosit de /recipes și /search.
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

    Gol nu înseamnă „main". O rețetă neclasificată trebuie să rămână găsibilă
    de sweep-ul de backfill, iar forțată pe „main" la citire n-o mai găsește.
    """
    value = (value or "").strip().lower()
    return value if value in COURSE_BY_ID else ""


def meals_for(course: str) -> list:
    return COURSE_BY_ID.get(normalize(course), {}).get("meals", [])


def courses_for_meal(meal: str) -> list:
    """Ce tipuri de fel se potrivesc la o masă. Inversul lui `meals_for`."""
    meal = (meal or "").strip().lower()
    return [c["id"] for c in COURSES if meal in c["meals"]]


# ---------- clasificarea euristică a rețetelor vechi ----------
#
# Rulează o singură dată, la migrare, ca sute de rețete existente să nu apară
# drept neclasificate în ziua în care apare filtrul. Analizorul AI e mai bun și
# le rescrie la următorul sweep.
#
# Conținutul din DB e în engleză, dar rețetele de dinaintea traducerii au rămas
# în original, deci lista include și cuvinte românești.
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
    """Ghicește cursul din titlu, cu descrierea și ingredientele ca sprijin.

    Ordinea din `_KEYWORDS` contează: „soup" înainte de „salad", fiindcă
    „ciorbă de salată verde" e o ciorbă. Fără potrivire cade pe felul
    principal, categoria cea mai largă și cel mai puțin greșit implicit.
    """
    haystack = " ".join([
        (title or ""),
        (description or ""),
        " ".join(str(i) for i in (ingredients or [])),
    ]).lower()
    # Titlul cântărește mai mult. „Chocolate cake" cu făină în ingrediente e
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
    """Vocabularul complet, trimis frontendului o singură dată."""
    return [dict(c) for c in COURSES]


# ---------- filtrul comun listei și căutării ----------

def apply_facets(query, recipe_model, course: str, meal: str,
                 kcal_min: int = 0, kcal_max: int = 0):
    """Filtrele „ce fel de mâncare" și „câte calorii".

    Stă aici, nu în routerul de rețete, fiindcă îl folosesc și /recipes, și
    /search. Un router care importă alt router ca să ajungă la o funcție cu
    underscore e o dependență pe care n-o caută nimeni.

    `course` acceptă mai multe valori separate prin virgulă. Sunt bife, nu un
    radio: „desert sau gustare" e o întrebare rezonabilă. `meal` e traducerea
    lor în tipuri de fel.

    Plafonul de calorii ignoră rețetele cu 0 kcal. Zero nu înseamnă „foarte
    ușoară", înseamnă „încă neanalizată", iar un filtru „sub 400 kcal" plin de
    rețete fără date ar fi mai rău decât unul mai scurt.
    """
    wanted = [c for c in (normalize(x) for x in (course or "").split(",")) if c]
    if meal:
        from_meal = courses_for_meal(meal)
        wanted = [c for c in wanted if c in from_meal] if wanted else from_meal
        if not wanted:
            # masă necunoscută. Mai bine niciun rezultat decât toate.
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
