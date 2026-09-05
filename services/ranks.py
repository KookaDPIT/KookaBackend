"""Sistemul de rank-uri (Copper I → Chef).

Rank-ul înlocuiește vechiul `level`: e o funcție pură de `User.xp_total`, deci
nu se poate desincroniza de progres — nu-l stocăm nicăieri, îl calculăm.

Sunt 16 trepte („tiers"): 5 rank-uri cu câte 3 divizii + Chef, care e unul
singur. `tier` = indexul 0..15; `rank` = familia (copper/bronze/.../chef).

Rețetele folosesc doar cele 6 familii, fără divizii — vezi `RECIPE_RANKS`.
"""

# ---------- familiile de rank ----------
# `faded`/`vibrant`: culorile pătrățelelor de progres din bara de rank.
RANKS = [
    {"id": "copper",   "name": "Copper",   "divisions": 3, "faded": "#d9a8a0", "vibrant": "#d74d34"},
    {"id": "bronze",   "name": "Bronze",   "divisions": 3, "faded": "#d4b5a0", "vibrant": "#b8753d"},
    {"id": "silver",   "name": "Silver",   "divisions": 3, "faded": "#d5d0c8", "vibrant": "#8b8882"},
    {"id": "gold",     "name": "Gold",     "divisions": 3, "faded": "#dcc793", "vibrant": "#c9a632"},
    {"id": "platinum", "name": "Platinum", "divisions": 3, "faded": "#d0e8f2", "vibrant": "#4fa3c8"},
    {"id": "chef",     "name": "Chef",     "divisions": 1, "faded": "#e6cde0", "vibrant": "#d16ba8"},
]

RANK_IDS = [r["id"] for r in RANKS]
RANK_BY_ID = {r["id"]: r for r in RANKS}

# XP cumulat necesar pentru fiecare din cele 16 trepte.
#
# Pragurile NU sunt alese estetic: fiecare e calibrat sub XP-ul total pe care
# lecțiile de sub el îl pot oferi (vezi `_tools/check_progression.py`). Altfel
# arborele se auto-blochează — o primă calibrare „rotundă" oprea utilizatorul
# după două lecții, fără nimic disponibil și fără cale de deblocare.
#
# Regula de proiectare: lecțiile singure trebuie să ducă până la Platinum III,
# iar mastery-ul și provocările zilnice sunt accelerare, nu obligații. Chef e
# singura treaptă care le cere explicit — de aici saltul de la final.
TIER_XP = [
    0,      # Copper I
    180,    # Copper II
    480,    # Copper III
    1000,   # Bronze I
    1650,   # Bronze II
    2400,   # Bronze III
    3300,   # Silver I
    4300,   # Silver II
    5400,   # Silver III
    6600,   # Gold I
    7900,   # Gold II
    9200,   # Gold III
    9900,   # Platinum I
    10600,  # Platinum II
    11600,  # Platinum III
    25000,  # Chef — cere și mastery, și provocări zilnice
]

TIER_COUNT = len(TIER_XP)          # 16
MAX_TIER = TIER_COUNT - 1          # 15

ROMAN = ["I", "II", "III"]


def _tier_parts(tier: int):
    """(rank_index, division_index) pentru o treaptă 0..15."""
    tier = max(0, min(MAX_TIER, int(tier)))
    remaining = tier
    for rank_index, rank in enumerate(RANKS):
        if remaining < rank["divisions"]:
            return rank_index, remaining
        remaining -= rank["divisions"]
    return len(RANKS) - 1, 0


def tier_for_xp(xp: int) -> int:
    """Cea mai mare treaptă al cărei prag e atins de `xp`."""
    xp = max(0, int(xp or 0))
    tier = 0
    for i, threshold in enumerate(TIER_XP):
        if xp >= threshold:
            tier = i
        else:
            break
    return tier


def tier_label(tier: int) -> str:
    """„Silver II", „Chef"."""
    rank_index, division = _tier_parts(tier)
    rank = RANKS[rank_index]
    if rank["divisions"] == 1:
        return rank["name"]
    return f"{rank['name']} {ROMAN[division]}"


def rank_id_for_tier(tier: int) -> str:
    return RANKS[_tier_parts(tier)[0]]["id"]


def first_tier_of_rank(rank_id: str) -> int:
    """Treapta la care începe o familie de rank — pragul folosit de rețete,
    care au rank fără divizii (o rețetă „Silver" cere Silver I)."""
    tier = 0
    for rank in RANKS:
        if rank["id"] == rank_id:
            return tier
        tier += rank["divisions"]
    return 0


def progress_for_xp(xp: int) -> dict:
    """Tot ce-i trebuie interfeței ca să deseneze bara de rank."""
    xp = max(0, int(xp or 0))
    tier = tier_for_xp(xp)
    rank_index, division = _tier_parts(tier)
    floor_xp = TIER_XP[tier]
    is_max = tier >= MAX_TIER
    next_xp = None if is_max else TIER_XP[tier + 1]
    span = 0 if is_max else next_xp - floor_xp
    into = xp - floor_xp
    return {
        "xp_total": xp,
        "tier": tier,
        "tier_label": tier_label(tier),
        "rank": RANKS[rank_index]["id"],
        "rank_name": RANKS[rank_index]["name"],
        "division": division + 1,
        "divisions": RANKS[rank_index]["divisions"],
        "tier_floor_xp": floor_xp,
        "next_tier_xp": next_xp,
        "xp_into_tier": into,
        "xp_to_next": None if is_max else max(0, next_xp - xp),
        # 100% când ești la Chef: bara e plină, nu goală
        "percent": 100 if is_max else (round(into / span * 100) if span else 0),
        "is_max": is_max,
    }


def table() -> list:
    """Tabelul complet al treptelor — trimis frontend-ului o singură dată."""
    out = []
    for tier, threshold in enumerate(TIER_XP):
        rank_index, division = _tier_parts(tier)
        rank = RANKS[rank_index]
        out.append({
            "tier": tier,
            "rank": rank["id"],
            "rank_name": rank["name"],
            "division": division + 1,
            "label": tier_label(tier),
            "xp": threshold,
            "faded": rank["faded"],
            "vibrant": rank["vibrant"],
        })
    return out


# ---------- rank-ul rețetelor (fără divizii) ----------
RECIPE_RANKS = RANK_IDS  # copper..chef

# Rețetele vechi au doar easy/medium/hard; le mapăm o singură dată, la migrare.
DIFFICULTY_TO_RANK = {
    "easy": "copper",
    "medium": "silver",
    "hard": "platinum",
}


def normalize_recipe_rank(value: str, difficulty: str = "") -> str:
    """Acceptă un rank valid, altfel cade pe maparea din dificultate."""
    if value and value in RANK_BY_ID:
        return value
    return DIFFICULTY_TO_RANK.get((difficulty or "").lower(), "copper")


def can_access_recipe(user_xp: int, recipe_rank: str) -> bool:
    """Rețetele peste rank-ul tău sunt blocate (decizie de produs, asumată)."""
    return tier_for_xp(user_xp) >= first_tier_of_rank(recipe_rank)
