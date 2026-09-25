# -*- coding: utf-8 -*-
"""Conținutul arborelui Learn: o rădăcină și 8 ramuri tehnice, 50 de lecții.

Fiecare lecție are conținut real, adică intro, pași și tips, un quiz de
trecere și unul de mastery, mai greu.

Poziția în fagure nu se scrie de mână. Ramura dă coloana, iar ordinea în listă
dă adâncimea. services/learn.py traduce perechea în coordonate axiale.

Prerechizita implicită e lecția precedentă din ramură, iar prima din ramură
depinde de rădăcină. `extra` adaugă legături între ramuri, și ele dau
fagurelui aspectul de rețea, nu de opt liste paralele.

`req_tier` e treapta minimă de rank, 0 e Copper I și 15 e Chef. XP-ul se
calculează din ea în services/learn.py, ca să rămână coerent pe tot arborele.

Conținutul e în engleză, ca restul conținutului. Doar chrome-ul interfeței
trece prin i18n.
"""
from data.branch_core import LESSONS as _CORE
from data.branch_mid import LESSONS as _MID
from data.branch_craft import LESSONS as _CRAFT
from data.branch_finish import LESSONS as _FINISH

# `angle` e direcția în care crește ramura, în grade de ecran: 0 la dreapta,
# 90 în jos, 180 la stânga, 270 în sus. Foundations stă în centru, iar cele
# opt ramuri pleacă din el, la 45 de grade una de alta.
#
# Ordinea pe cerc nu e arbitrară. Câteva lecții depind de o lecție din altă
# ramură, prin `extra`, iar legăturile alea se desenează ca linii peste
# planșă. Două ramuri legate, puse față în față, ar da o linie care taie prin
# mijloc.
#
# Ordinea de mai jos scurtează distanța totală a legăturilor: vecinii de aici
# sunt ramuri care chiar depind una de alta, sosuri lângă ouă și plating,
# căldură lângă fonduri, pâine lângă fermentație. Knife Skills n-are legături
# încrucișate, deci ia locul rămas.
BRANCHES = [
    {"id": "eggs",    "name": "Eggs & Dairy",              "icon": "🥚", "color": "#e0a92a", "angle": 270},
    {"id": "sauce",   "name": "Sauces & Emulsions",        "icon": "🥣", "color": "#b8894a", "angle": 315},
    {"id": "plate",   "name": "Plating & Pastry",          "icon": "🍰", "color": "#c06a92", "angle": 0},
    {"id": "heat",    "name": "Heat & Searing",            "icon": "🔥", "color": "#d97706", "angle": 45},
    {"id": "stock",   "name": "Stocks & Soups",            "icon": "🍲", "color": "#5f8f8a", "angle": 90},
    {"id": "bake",    "name": "Baking & Bread",            "icon": "🍞", "color": "#a4703c", "angle": 135},
    {"id": "ferment", "name": "Fermentation & Preserving", "icon": "🫙", "color": "#7d9a5a", "angle": 180},
    {"id": "knife",   "name": "Knife Skills",              "icon": "🔪", "color": "#c2603f", "angle": 225},
]

# Rădăcina fagurelui, singura lecție fără prerechizite.
ROOT = {
    "slug": "foundations",
    "branch": "root",
    "title": "Foundations",
    "icon": "🍳",
    "req_tier": 0,
    "est_min": 20,
    "summary": "Salt, fat, acid, heat — the four dials every dish turns on, and how to taste your way between them.",
    "intro": (
        "Before any technique there is one skill that outranks the rest: tasting, and knowing what to "
        "change when something is off. Nearly every 'bland' dish is under-salted, every 'heavy' dish is "
        "missing acid, and every 'flat' dish never got enough heat to build browning. Learn to name the "
        "problem and the fix becomes obvious."
    ),
    "steps": [
        "Salt in layers: a little at each stage seasons the food itself, while all the salt at the end only seasons the surface.",
        "Taste a spoonful, then taste it again with one extra grain of salt on your tongue — that comparison teaches your palate faster than any recipe.",
        "When a dish tastes rich but dull, add acid (lemon, vinegar, yoghurt) before you add more salt.",
        "Fat carries flavour: aromatics bloomed in oil or butter spread through the whole pot, water does not.",
        "Heat is a tool with settings — high for browning and searing, low for tenderising and rendering.",
        "Write down what you changed. Cooking improves through repetition with notes, not through new recipes.",
    ],
    "tips": [
        "Keep salt in an open bowl, not a shaker. You season more accurately with your fingers.",
        "If you over-salt, add bulk (more liquid, potato, unsalted starch) — never more acid to 'balance' it.",
    ],
    "quiz": [
        {"q": "Which four elements does great cooking balance?",
         "options": ["Salt, fat, acid, heat", "Sugar, oil, water, ice", "Flour, egg, milk, butter", "Pepper, garlic, onion, wine"],
         "correct": 0},
        {"q": "A dish tastes rich and heavy but somehow dull. Your first move is to add…",
         "options": ["More salt", "Acid", "More fat", "Sugar"],
         "correct": 1},
        {"q": "Why season in layers instead of all at the end?",
         "options": ["It uses less salt overall", "It seasons the food itself, not just the surface", "It stops food from burning", "It makes food cook faster"],
         "correct": 1},
    ],
    "mastery_quiz": [
        {"q": "You over-salted a soup. The reliable fix is to…",
         "options": ["Add lemon juice to balance it", "Add sugar", "Add unsalted bulk — more liquid, potato or starch", "Boil it down further"],
         "correct": 2},
        {"q": "Blooming spices in hot fat before adding liquid works because…",
         "options": ["Fat dissolves flavour compounds water cannot", "It sterilises the spices", "It removes bitterness entirely", "It makes them dissolve in water"],
         "correct": 0},
        {"q": "Two cooks follow the same recipe and get different results. The most likely cause is…",
         "options": ["Different brands of salt", "Different pan sizes and heat levels", "Different bowls", "Different measuring spoons"],
         "correct": 1},
    ],
}

# Ordinea contează: în cadrul unei ramuri, poziția în listă e adâncimea.
LESSONS = _CORE + _MID + _CRAFT + _FINISH

ALL_NODES = [ROOT] + LESSONS
