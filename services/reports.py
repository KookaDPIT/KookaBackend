"""Raportări de conținut: vocabularul motivelor și citirea unei cozi.

Motivele sunt o listă fixă, cu chei stabile. Moderatorii filtrează după ele,
iar textul se traduce în frontend. „other" cere detalii, fiindcă un raport
fără motiv și fără explicație nu se poate trata.
"""

REASONS = [
    {"id": "spam", "needs_details": False},
    {"id": "offensive", "needs_details": False},
    {"id": "dangerous", "needs_details": False},
    {"id": "not_a_recipe", "needs_details": False, "targets": ["recipe"]},
    {"id": "stolen", "needs_details": False},
    {"id": "other", "needs_details": True},
]

REASON_IDS = {r["id"] for r in REASONS}

TARGET_TYPES = ("recipe", "forum_post", "forum_comment")


def normalize_reason(value: str) -> str:
    value = (value or "").strip().lower()
    return value if value in REASON_IDS else "other"


def table(target_type: str = "") -> list:
    """Motivele valabile pentru un tip de obiect.

    `targets` le restrânge pe unele. „Nu e o rețetă" n-are sens pe o postare.
    """
    out = []
    for reason in REASONS:
        targets = reason.get("targets")
        if targets and target_type and target_type not in targets:
            continue
        out.append({"id": reason["id"], "needs_details": reason["needs_details"]})
    return out
