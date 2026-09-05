# -*- coding: utf-8 -*-
"""Verifică faptul că arborele Learn poate fi terminat.

Rulează o simulare lacomă: un utilizator care termină tot ce-i devine
disponibil, folosind DOAR XP-ul din lecții — fără mastery, fără provocări
zilnice. Dacă simularea se blochează, pragurile din `services.ranks.TIER_XP`
cer mai mult XP decât pot produce lecțiile de sub ele, iar utilizatorul rămâne
împotmolit fără nicio cale de deblocare.

Rulare (din rădăcina backendului):

    python -m _tools.check_progression

Ieșire 0 = arborele e parcurgibil. Rulează asta după orice schimbare de
`TIER_XP`, de `req_tier` sau de formula de XP.
"""
import sys

# Consola Windows implicită e cp1252 și nu poate scrie diacritice; fără asta
# scriptul crapă la primul `print`, nu la o problemă reală de progresie.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data import lessons_seed
from services import learn, ranks


def build_nodes():
    """Reconstruiește lecțiile din seed, fără să atingă baza de date."""
    nodes = []
    prev_in_branch = {}
    depth_by_branch = {}
    for node in lessons_seed.ALL_NODES:
        branch = node.get("branch", "root")
        if branch == "root":
            prereqs = []
        else:
            depth_by_branch[branch] = depth_by_branch.get(branch, 0) + 1
            parent = prev_in_branch.get(branch, lessons_seed.ROOT["slug"])
            prereqs = [parent] + list(node.get("extra", []))
            prev_in_branch[branch] = node["slug"]
        nodes.append({
            "slug": node["slug"],
            "req_tier": node["req_tier"],
            "xp": learn.xp_for_tier(node["req_tier"]),
            "mastery_xp": learn.mastery_xp_for_tier(node["req_tier"]),
            "prereqs": prereqs,
        })
    return nodes


def simulate(nodes):
    xp = 0
    done = set()
    rounds = 0
    while True:
        tier = ranks.tier_for_xp(xp)
        available = [
            n for n in nodes
            if n["slug"] not in done
            and all(p in done for p in n["prereqs"])
            and tier >= n["req_tier"]
        ]
        if not available:
            return xp, done, rounds
        for node in available:
            done.add(node["slug"])
            xp += node["xp"]
        rounds += 1


def main():
    nodes = build_nodes()
    xp, done, rounds = simulate(nodes)
    total = len(nodes)
    tier = ranks.tier_for_xp(xp)

    print(f"lecții terminate : {len(done)}/{total}")
    print(f"XP din lecții    : {xp}")
    print(f"rank atins       : {ranks.tier_label(tier)}")
    print(f"runde            : {rounds}")

    lesson_xp = sum(n["xp"] for n in nodes)
    mastery_xp = sum(n["mastery_xp"] for n in nodes)
    print(f"plafon lecții    : {lesson_xp}  (+{mastery_xp} din mastery = {lesson_xp + mastery_xp})")
    print(f"prag Chef        : {ranks.TIER_XP[-1]}"
          f"  -> mai trebuie {max(0, ranks.TIER_XP[-1] - lesson_xp - mastery_xp)} XP din provocări")

    stuck = [n for n in nodes if n["slug"] not in done]
    if stuck:
        print(f"\nEȘEC: {len(stuck)} lecții inaccesibile. Primele blocaje:")
        for node in stuck[:8]:
            print(f"  {node['slug']}: cere {ranks.tier_label(node['req_tier'])}, "
                  f"utilizatorul e blocat la {ranks.tier_label(tier)}")
        return 1

    print("\nOK: tot arborele e parcurgibil doar din XP-ul lecțiilor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
