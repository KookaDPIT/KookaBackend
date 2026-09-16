# -*- coding: utf-8 -*-
"""Trofeele — pe modelul PlayStation: bronz, argint, aur, ascunse, platină.

Structura, și de ce e așa
-------------------------
Un trofeu e o întrebare despre istoricul unui utilizator. Sunt 60+ de
întrebări, iar dacă fiecare și-ar interoga singură baza de date, deschiderea
paginii ar însemna 60 de interogări.

Deci se strâng o dată toate faptele (`collect_facts`) și fiecare trofeu e o
funcție pură peste dicționarul ăla. Adăugarea unui trofeu nou înseamnă o linie
în catalog; dacă are nevoie de o informație nouă, un singur câmp în facts.

Câștigarea se STOCHEAZĂ (`EarnedTrophy`), spre deosebire de rank și streak-uri
care se calculează. Motivul e că aici contează *când*: „ai câștigat Iron Chef"
e un eveniment care se anunță o dată, iar dacă ar fi recalculat la fiecare
cerere n-am ști niciodată dacă l-am anunțat deja. Evaluarea rămâne sursa
adevărului — rândul stocat notează doar momentul.

Platina e specială: se ia când toate celelalte sunt luate. Nu e o condiție
peste date, e o condiție peste trofee, deci se evaluează la urmă.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

import models
import serializers

BRONZE, SILVER, GOLD, HIDDEN, PLATINUM = "bronze", "silver", "gold", "hidden", "platinum"
TIERS = [BRONZE, SILVER, GOLD, HIDDEN, PLATINUM]

# Ordinea în care le arată interfața, și eticheta fiecărei grupe.
TIER_META = {
    BRONZE:   {"name": "Bronze",   "order": 0},
    SILVER:   {"name": "Silver",   "order": 1},
    GOLD:     {"name": "Gold",     "order": 2},
    HIDDEN:   {"name": "Hidden",   "order": 3},
    PLATINUM: {"name": "Platinum", "order": 4},
}


# ==========================================================================
# FAPTELE
# ==========================================================================

def _day(dt):
    return dt.date() if isinstance(dt, datetime) else None


def collect_facts(db: Session, user: models.User) -> dict:
    """Tot ce le trebuie trofeelor, în cât mai puține interogări.

    Câmpurile sunt numite după întrebare, nu după tabelă: `cuisines` nu
    `distinct_recipe_origins`, pentru că predicatele de mai jos se citesc mai
    ușor așa și ele sunt partea care se schimbă des.
    """
    uid = user.id

    # ---- gătit ----
    cook_rows = (
        db.query(models.CookLog, models.Recipe)
        .join(models.Recipe, models.Recipe.id == models.CookLog.recipe_id)
        .filter(models.CookLog.user_id == uid)
        .all()
    )
    cook_days = sorted({_day(c.cooked_at) for c, _ in cook_rows if c.cooked_at})
    per_recipe = {}
    for c, _ in cook_rows:
        per_recipe[c.recipe_id] = per_recipe.get(c.recipe_id, 0) + 1

    cuisines = {}
    courses_cooked = set()
    cooked_hours = []
    ingredient_set = set()
    allergen_free_cooks = 0
    onion_heavy = 0
    garlic_bread = 0
    for c, r in cook_rows:
        if r.origin:
            cuisines[r.origin] = cuisines.get(r.origin, 0) + 1
        if r.course:
            courses_cooked.add(r.course)
        if c.cooked_at:
            cooked_hours.append(c.cooked_at.hour)
        ings = serializers._load_json(r.ingredients, [])
        for ing in ings:
            ingredient_set.add(str(ing).strip().lower())
        allergens = serializers._load_json(r.allergens, {})
        if not (allergens.get("contains") or []):
            allergen_free_cooks += 1
        # „The Onion Incident": 5+ cepe într-o singură rețetă
        for ing in ings:
            text = str(ing).lower()
            if "onion" in text or "ceap" in text:
                digits = "".join(ch for ch in text if ch.isdigit())
                if digits and int(digits[:3]) >= 5:
                    onion_heavy += 1
                    break
        title = (r.title or "").lower()
        if "garlic bread" in title or "pâine cu usturoi" in title or "paine cu usturoi" in title:
            garlic_bread += 1

    # ---- sesiuni de cook-along ----
    sessions = (
        db.query(models.CookSession)
        .filter(models.CookSession.user_id == uid)
        .all()
    )
    finished = [s for s in sessions if s.finished_at]
    gave_up = [s for s in sessions if s.gave_up_at and not s.finished_at]
    # „Comeback Kid" / „Second Try": ai abandonat o rețetă și ai terminat-o mai
    # târziu. Compararea se face pe rețetă, nu pe sesiune.
    gave_up_recipes = {s.recipe_id for s in gave_up}
    finished_recipes = {s.recipe_id for s in finished}
    comebacks = gave_up_recipes & finished_recipes

    durations = {}
    for s in finished:
        if s.started_at and s.finished_at:
            durations[s.id] = (s.finished_at - s.started_at).total_seconds() / 60

    # ---- lecții, provocări, recenzii, rețete proprii ----
    lessons_done = (
        db.query(models.LessonProgress)
        .filter(
            models.LessonProgress.user_id == uid,
            models.LessonProgress.completed.is_(True),
        )
        .count()
    )
    lesson_branches = (
        db.query(models.Lesson.branch)
        .join(models.LessonProgress, models.LessonProgress.lesson_id == models.Lesson.id)
        .filter(
            models.LessonProgress.user_id == uid,
            models.LessonProgress.completed.is_(True),
        )
        .all()
    )
    branch_done = {}
    for (branch,) in lesson_branches:
        branch_done[branch] = branch_done.get(branch, 0) + 1
    branch_total = {}
    for branch, total in db.query(models.Lesson.branch, models.Lesson.id).all():
        branch_total[branch] = branch_total.get(branch, 0) + 1
    full_branch = any(
        count >= branch_total.get(branch, 10**9) and count > 0
        for branch, count in branch_done.items()
    )

    challenges_done = (
        db.query(models.DailyChallengeDone)
        .filter(models.DailyChallengeDone.user_id == uid)
        .count()
    )

    my_reviews = (
        db.query(models.Review).filter(models.Review.user_id == uid).all()
    )
    my_recipe_ids = [
        rid for (rid,) in db.query(models.Recipe.id).filter(models.Recipe.author_id == uid).all()
    ]
    reviews_on_mine = (
        db.query(models.Review)
        .filter(models.Review.recipe_id.in_(my_recipe_ids or [0]))
        .filter(models.Review.user_id != uid)
        .count()
    )

    # ---- AI ----
    ai_messages = (
        db.query(models.ChatMessage)
        .join(
            models.ChatConversation,
            models.ChatConversation.id == models.ChatMessage.conversation_id,
        )
        .filter(
            models.ChatConversation.user_id == uid,
            models.ChatMessage.role == "user",
        )
        .all()
    )
    photo_messages = [m for m in ai_messages if m.has_photo]

    # ---- planificator ----
    planned = (
        db.query(models.MealPlanEntry)
        .filter(models.MealPlanEntry.user_id == uid)
        .all()
    )
    planned_days = {}
    for entry in planned:
        planned_days.setdefault(entry.date, set()).add(entry.slot)
    shopping = (
        db.query(models.ShoppingItem)
        .filter(models.ShoppingItem.user_id == uid)
        .count()
    )

    bookmarks = (
        db.query(models.Bookmark).filter(models.Bookmark.user_id == uid).count()
    )
    cooked_recipe_ids = set(per_recipe)
    bookmarked_uncooked = (
        db.query(models.Bookmark)
        .filter(
            models.Bookmark.user_id == uid,
            models.Bookmark.recipe_id.notin_(cooked_recipe_ids or [0]),
        )
        .count()
    )

    forum_comments = (
        db.query(models.ForumComment).filter(models.ForumComment.author_id == uid).count()
    )

    # cea mai lungă pauză între două zile de gătit
    longest_gap = 0
    for a, b in zip(cook_days, cook_days[1:]):
        longest_gap = max(longest_gap, (b - a).days)

    return {
        "user": user,
        "allergies_set": bool((user.allergies or "").strip()),
        "own_origin": (user.language or "").lower(),

        "cooks": len(cook_rows),
        "cook_days": cook_days,
        "cook_day_set": set(cook_days),
        "per_recipe": per_recipe,
        "max_repeat": max(per_recipe.values()) if per_recipe else 0,
        "cuisines": cuisines,
        "courses_cooked": courses_cooked,
        "cooked_hours": cooked_hours,
        "ingredients": ingredient_set,
        "allergen_free_cooks": allergen_free_cooks,
        "onion_heavy": onion_heavy,
        "garlic_bread": garlic_bread,
        "longest_gap": longest_gap,

        "sessions": sessions,
        "finished_sessions": finished,
        "gave_up_recipes": gave_up_recipes,
        "comebacks": comebacks,
        "durations": durations,

        "lessons_done": lessons_done,
        "full_branch": full_branch,
        "challenges_done": challenges_done,

        "my_reviews": my_reviews,
        "reviews_with_photo": sum(1 for r in my_reviews if (r.photo_url or "").strip()),
        "my_recipes": len(my_recipe_ids),
        "reviews_on_mine": reviews_on_mine,

        "ai_asks": len(ai_messages),
        "ai_photos": len(photo_messages),

        "planned": len(planned),
        "planned_days": planned_days,
        "shopping_items": shopping,
        "bookmarks": bookmarks,
        "bookmarked_uncooked": bookmarked_uncooked,
        "forum_comments": forum_comments,
    }


# ==========================================================================
# PREDICATE AJUTĂTOARE
# ==========================================================================

def _streak_days(days: set, length: int) -> bool:
    """Există `length` zile consecutive oriunde în istoric?"""
    for day in days:
        if all((day + timedelta(days=i)) in days for i in range(length)):
            return True
    return False


def _weekday_cook(f) -> bool:
    return any(d.weekday() < 5 for d in f["cook_day_set"])


def _weekend_pair(f) -> bool:
    """Sâmbătă ȘI duminică — nu neapărat în același weekend, ca „Weekend Chef"
    să nu depindă de a găti de două ori în 48 de ore."""
    days = f["cook_day_set"]
    return any(d.weekday() == 5 for d in days) and any(d.weekday() == 6 for d in days)


def _cooked_between(f, start_hour: int, end_hour: int) -> bool:
    """Ore locale-UTC. Intervalul poate trece peste miezul nopții."""
    for hour in f["cooked_hours"]:
        if start_hour <= end_hour:
            if start_hour <= hour < end_hour:
                return True
        elif hour >= start_hour or hour < end_hour:
            return True
    return False


def _count_between(f, start_hour: int, end_hour: int) -> int:
    n = 0
    for hour in f["cooked_hours"]:
        if start_hour <= end_hour:
            n += 1 if start_hour <= hour < end_hour else 0
        else:
            n += 1 if (hour >= start_hour or hour < end_hour) else 0
    return n


def _fast_finish(f) -> bool:
    """Terminat în sub jumătate din timpul estimat al rețetei.

    Pragul de 3 minute există pentru că o sesiune deschisă și încheiată imediat
    (ai gătit înainte, ai venit doar să încarci poza) ar lua trofeul fără să fi
    gătit nimic repede.
    """
    for s in f["finished_sessions"]:
        minutes = f["durations"].get(s.id)
        estimate = f["estimates"].get(s.id)
        if minutes is None or not estimate:
            continue
        if 3 <= minutes <= estimate / 2:
            return True
    return False


def _slow_finish(f) -> bool:
    for s in f["finished_sessions"]:
        minutes = f["durations"].get(s.id)
        estimate = f["estimates"].get(s.id)
        if minutes is not None and estimate and minutes >= estimate * 2.5:
            return True
    return False


# ==========================================================================
# CATALOGUL
# ==========================================================================
# `check` primește `facts` și întoarce bool. `progress` (opțional) întoarce
# (curent, țintă) ca bara să arate cât mai ai — un trofeu care cere 30 de
# provocări e o promisiune mai bună decât o promisiune tăcută.

def _T(id, tier, name, desc, check, progress=None):
    return {
        "id": id, "tier": tier, "name": name, "description": desc,
        "check": check, "progress": progress,
    }


CATALOGUE = [
    # ---------------- BRONZE (20) ----------------
    _T("first_bite", BRONZE, "First Bite", "Cook your first recipe.",
       lambda f: f["cooks"] >= 1, lambda f: (f["cooks"], 1)),
    _T("say_cheese", BRONZE, "Say Cheese", "Scan your first meal for calories.",
       lambda f: f["ai_photos"] >= 1, lambda f: (f["ai_photos"], 1)),
    _T("outsourced", BRONZE, "Outsourced My Braincells", "Ask the Kooka AI for help.",
       lambda f: f["ai_asks"] >= 1, lambda f: (f["ai_asks"], 1)),
    _T("challenger", BRONZE, "Challenger", "Complete your first daily challenge.",
       lambda f: f["challenges_done"] >= 1, lambda f: (f["challenges_done"], 1)),
    _T("three_squares", BRONZE, "Three Squares",
       "Plan breakfast, lunch and dinner on the same day.",
       lambda f: any(
           {"breakfast", "lunch", "dinner"} <= slots for slots in f["planned_days"].values()
       )),
    _T("shopping_list", BRONZE, "Shopping List", "Put a recipe on your shopping list.",
       lambda f: f["shopping_items"] >= 1, lambda f: (f["shopping_items"], 1)),
    _T("snap_happy", BRONZE, "Snap Happy", "Photograph a finished dish.",
       lambda f: len(f["finished_sessions"]) >= 1 or f["cooks"] >= 1),
    _T("breakfast_club", BRONZE, "Breakfast Club", "Cook a breakfast dish.",
       lambda f: "breakfast" in f["courses_cooked"]),
    _T("midnight_snack", BRONZE, "Midnight Snack", "Finish a dish after 10pm.",
       lambda f: _cooked_between(f, 22, 2)),
    _T("twos_company", BRONZE, "Two's Company", "Cook the same recipe twice.",
       lambda f: f["max_repeat"] >= 2, lambda f: (f["max_repeat"], 2)),
    _T("new_kid", BRONZE, "New Kid in the Kitchen", "Tell us about your allergens.",
       lambda f: f["allergies_set"]),
    _T("around_the_block", BRONZE, "Around the Block",
       "Cook something from a cuisine other than your own.",
       lambda f: len(f["cuisines"]) >= 2, lambda f: (len(f["cuisines"]), 2)),
    _T("locked_in", BRONZE, "Locked In Cookin'",
       "Finish a recipe start to finish without leaving the app.",
       lambda f: any(not s.left_app for s in f["finished_sessions"])),
    _T("show_and_tell", BRONZE, "Show and Tell", "Put a photo on a review.",
       lambda f: f["reviews_with_photo"] >= 1, lambda f: (f["reviews_with_photo"], 1)),
    _T("second_try", BRONZE, "Second Try", "Finish a recipe you had given up on.",
       lambda f: len(f["comebacks"]) >= 1, lambda f: (len(f["comebacks"]), 1)),
    _T("weekday_warrior", BRONZE, "Weekday Warrior", "Cook on a weekday.",
       _weekday_cook),
    _T("weekend_chef", BRONZE, "Weekend Chef", "Cook on a Saturday and on a Sunday.",
       _weekend_pair),
    _T("under_500", BRONZE, "Under 500", "Cook a dish under 500 kcal a serving.",
       lambda f: _kcal_cooked(f, 0, 500)),
    _T("big_plate", BRONZE, "Big Plate", "Cook a dish over 1000 kcal a serving.",
       lambda f: _kcal_cooked(f, 1000, 10**6)),
    _T("solo_debut", BRONZE, "Solo Debut", "Publish your first original recipe.",
       lambda f: f["my_recipes"] >= 1, lambda f: (f["my_recipes"], 1)),

    # ---------------- SILVER (15) ----------------
    _T("meal_prep_machine", SILVER, "Meal Prep Machine", "Cook seven days in a row.",
       lambda f: _streak_days(f["cook_day_set"], 7)),
    _T("week_one_down", SILVER, "Week One Down", "Complete seven daily challenges.",
       lambda f: f["challenges_done"] >= 7, lambda f: (f["challenges_done"], 7)),
    _T("world_traveler", SILVER, "World Traveler", "Cook from five different cuisines.",
       lambda f: len(f["cuisines"]) >= 5, lambda f: (len(f["cuisines"]), 5)),
    _T("pantry_stocked", SILVER, "Pantry Stocked", "Cook with 15 different ingredients.",
       lambda f: len(f["ingredients"]) >= 15, lambda f: (len(f["ingredients"]), 15)),
    _T("comfortable", SILVER, "Comfortable in the Kitchen", "Cook 20 recipes.",
       lambda f: f["cooks"] >= 20, lambda f: (f["cooks"], 20)),
    _T("skill_builder", SILVER, "Skill Builder", "Complete five lessons.",
       lambda f: f["lessons_done"] >= 5, lambda f: (f["lessons_done"], 5)),
    _T("graduate", SILVER, "Graduate", "Complete a whole lesson branch.",
       lambda f: f["full_branch"]),
    _T("regular", SILVER, "Regular", "Cook 30 recipes.",
       lambda f: f["cooks"] >= 30, lambda f: (f["cooks"], 30)),
    _T("show_up", SILVER, "Show Up", "Get a review on a recipe you published.",
       lambda f: f["reviews_on_mine"] >= 1, lambda f: (f["reviews_on_mine"], 1)),
    _T("recipe_collector", SILVER, "Recipe Collector", "Plan 25 meals in your calendar.",
       lambda f: f["planned"] >= 25, lambda f: (f["planned"], 25)),
    _T("comeback_kid", SILVER, "Comeback Kid",
       "Give up on a recipe, come back, and finish it.",
       lambda f: len(f["comebacks"]) >= 1, lambda f: (len(f["comebacks"]), 1)),
    _T("no_hand_holding", SILVER, "No Hand-Holding",
       "Finish ten recipes without asking the AI for help.",
       lambda f: _quiet_finishes(f) >= 10, lambda f: (_quiet_finishes(f), 10)),
    _T("cookbook_starter", SILVER, "Cookbook Starter", "Publish five original recipes.",
       lambda f: f["my_recipes"] >= 5, lambda f: (f["my_recipes"], 5)),
    _T("consistent", SILVER, "Consistent", "Cook fourteen days in a row.",
       lambda f: _streak_days(f["cook_day_set"], 14)),
    _T("balanced_diet", SILVER, "Balanced Diet",
       "Cook across five different kinds of dish.",
       lambda f: len(f["courses_cooked"]) >= 5, lambda f: (len(f["courses_cooked"]), 5)),

    # ---------------- GOLD (5) ----------------
    _T("iron_chef", GOLD, "Iron Chef", "Complete thirty daily challenges.",
       lambda f: f["challenges_done"] >= 30, lambda f: (f["challenges_done"], 30)),
    _T("local_legend", GOLD, "Local Legend", "Cook fifty dishes from one cuisine.",
       lambda f: max(f["cuisines"].values(), default=0) >= 50,
       lambda f: (max(f["cuisines"].values(), default=0), 50)),
    _T("around_the_world", GOLD, "Around the World", "Cook from twenty cuisines.",
       lambda f: len(f["cuisines"]) >= 20, lambda f: (len(f["cuisines"]), 20)),
    _T("three_six_five", GOLD, "365", "Cook 365 dishes.",
       lambda f: f["cooks"] >= 365, lambda f: (f["cooks"], 365)),
    _T("cookbook_author", GOLD, "Cookbook Author", "Publish ten original recipes.",
       lambda f: f["my_recipes"] >= 10, lambda f: (f["my_recipes"], 10)),

    # ---------------- HIDDEN (24) ----------------
    _T("chaotic_neutral", HIDDEN, "Chaotic Neutral",
       "Finish a recipe without starting a single timer it offered you.",
       lambda f: any(
           s.timers_available > 0 and (s.timers_started or 0) == 0
           for s in f["finished_sessions"]
       )),
    _T("yes_chef", HIDDEN, "Yes Chef",
       "Ask the AI for help on every single step of a recipe.",
       lambda f: any(
           s.steps_total > 0 and (s.ai_steps or 0) >= s.steps_total
           for s in f["sessions"]
       )),
    _T("gordon_ramsay", HIDDEN, "The Gordon Ramsay Special",
       "Ask for help three or more times on one recipe.",
       lambda f: any((s.ai_asks or 0) >= 3 for s in f["sessions"])),
    _T("plot_twist", HIDDEN, "Plot Twist",
       "Have the AI turn down your photo of a finished dish.",
       lambda f: any((s.verify_failures or 0) >= 1 for s in f["sessions"])),
    _T("i_got_this", HIDDEN, "I Got This… Actually I Don't",
       "Ask for help within two minutes of starting.",
       lambda f: any(
           0 <= (s.first_ask_after or -1) <= 120 for s in f["sessions"]
       )),
    _T("quitters_club", HIDDEN, "Quitter's Club", "Give up on five different recipes.",
       lambda f: len(f["gave_up_recipes"]) >= 5, lambda f: (len(f["gave_up_recipes"]), 5)),
    _T("vampire_chef", HIDDEN, "Vampire Chef", "Finish a dish between 2 and 5am.",
       lambda f: _cooked_between(f, 2, 5)),
    _T("cereal_killer", HIDDEN, "Cereal Killer", "Cook breakfast ten times.",
       lambda f: _course_count(f, "breakfast") >= 10,
       lambda f: (_course_count(f, "breakfast"), 10)),
    _T("family_friendly", HIDDEN, "Family Friendly",
       "Cook a dish with no allergens at all.",
       lambda f: f["allergen_free_cooks"] >= 1),
    _T("onion_incident", HIDDEN, "The Onion Incident",
       "Cook something that wanted five or more onions.",
       lambda f: f["onion_heavy"] >= 1),
    _T("diet_starts_monday", HIDDEN, "Diet Starts Monday",
       "Cook a single serving over 2000 kcal.",
       lambda f: _kcal_cooked(f, 2000, 10**6)),
    _T("garlic_bread", HIDDEN, "Garlic Bread Enjoyer", "Cook garlic bread.",
       lambda f: f["garlic_bread"] >= 1),
    _T("speed_chef", HIDDEN, "Speed Chef",
       "Finish a recipe in under half its estimated time.",
       _fast_finish),
    _T("slow_and_steady", HIDDEN, "Slow and Steady",
       "Take more than twice the estimated time — and still finish.",
       _slow_finish),
    _T("mystery_meat", HIDDEN, "Mystery Meat",
       "Send the scanner a photo it cannot place.",
       lambda f: any((s.verify_failures or 0) >= 2 for s in f["sessions"])),
    _T("one_and_done", HIDDEN, "One and Done",
       "Finish a recipe first time, no giving up, no AI.",
       lambda f: any(
           (s.ai_asks or 0) == 0 and s.gave_up_at is None and s.finished_at
           and f["per_recipe"].get(s.recipe_id, 0) == 1
           for s in f["sessions"]
       )),
    _T("recipe_hoarder", HIDDEN, "Recipe Hoarder",
       "Save 100 recipes without cooking a single one of them.",
       lambda f: f["bookmarked_uncooked"] >= 100,
       lambda f: (f["bookmarked_uncooked"], 100)),
    _T("hat_trick", HIDDEN, "Hat-Trick Pony", "Cook the exact same recipe three times.",
       lambda f: f["max_repeat"] >= 3, lambda f: (f["max_repeat"], 3)),
    _T("ambitious", HIDDEN, "Ambitious", "Cook something well above your rank.",
       lambda f: _above_rank_cook(f)),
    _T("ghost_kitchen", HIDDEN, "Ghost Kitchen",
       "Go a week without cooking, then come back.",
       lambda f: f["longest_gap"] >= 7),
    _T("trash_talk", HIDDEN, "Trash Talk", "Comment on someone else's dish.",
       lambda f: f["forum_comments"] >= 1 or len(f["my_reviews"]) >= 1),
    _T("night_owl", HIDDEN, "Night Owl Snacker",
       "Three late-night dishes in one week.",
       lambda f: _count_between(f, 22, 5) >= 3, lambda f: (_count_between(f, 22, 5), 3)),
    _T("perfectionist", HIDDEN, "Perfectionist",
       "Have a dish photo confirmed on the very first try, ten times.",
       lambda f: _clean_verifies(f) >= 10, lambda f: (_clean_verifies(f), 10)),
    _T("water_boiler", HIDDEN, "Water Boiler",
       "Cook something that starts by boiling water.",
       lambda f: _boils_water(f)),
]

# Platina stă în afara catalogului: condiția ei e „toate celelalte", deci se
# evaluează după ce se știe rezultatul lor.
PLATINUM_TROPHY = {
    "id": "master_chef",
    "tier": PLATINUM,
    "name": "Master Chef",
    "description": "Earn every other trophy in Kooka.",
}

BY_ID = {t["id"]: t for t in CATALOGUE}


# ---------- predicate care au nevoie de faptele complete ----------

def _kcal_cooked(f, low: int, high: int) -> bool:
    return any(low <= kcal < high for kcal in f.get("cooked_kcal", []))


def _course_count(f, course: str) -> int:
    return f.get("course_counts", {}).get(course, 0)


def _quiet_finishes(f) -> int:
    return sum(1 for s in f["finished_sessions"] if (s.ai_asks or 0) == 0)


def _clean_verifies(f) -> int:
    return sum(
        1 for s in f["finished_sessions"] if (s.verify_failures or 0) == 0
    )


def _above_rank_cook(f) -> bool:
    return f.get("above_rank_cook", False)


def _boils_water(f) -> bool:
    return f.get("boils_water", False)


# ==========================================================================
# EVALUARE ȘI STOCARE
# ==========================================================================

def evaluate(db: Session, user: models.User) -> dict:
    """Ce are, ce nu are, cât mai are de făcut — plus platina.

    Salvează rândurile pentru trofeele nou câștigate, ca `earned_at` să fie o
    dată reală și nu „acum, de fiecare dată când deschizi pagina".
    """
    facts = collect_facts(db, user)
    _enrich(db, user, facts)

    earned_rows = {
        row.trophy_id: row
        for row in db.query(models.EarnedTrophy)
        .filter(models.EarnedTrophy.user_id == user.id)
        .all()
    }

    out = []
    all_earned = True
    fresh = []
    for trophy in CATALOGUE:
        try:
            has = bool(trophy["check"](facts))
        except Exception:
            # Un predicat care crapă pe date neașteptate nu trebuie să scoată
            # toată pagina de trofee din funcțiune.
            has = False
        if has and trophy["id"] not in earned_rows:
            row = models.EarnedTrophy(user_id=user.id, trophy_id=trophy["id"])
            db.add(row)
            earned_rows[trophy["id"]] = row
            fresh.append(trophy["id"])
        if not has:
            all_earned = False
        out.append(_shape(trophy, facts, earned_rows.get(trophy["id"]), has))

    # platina
    has_platinum = all_earned
    if has_platinum and PLATINUM_TROPHY["id"] not in earned_rows:
        row = models.EarnedTrophy(user_id=user.id, trophy_id=PLATINUM_TROPHY["id"])
        db.add(row)
        earned_rows[PLATINUM_TROPHY["id"]] = row
        fresh.append(PLATINUM_TROPHY["id"])
    out.append(
        _shape(
            {**PLATINUM_TROPHY, "check": None, "progress": None},
            facts,
            earned_rows.get(PLATINUM_TROPHY["id"]),
            has_platinum,
            progress_override=(sum(1 for t in out if t["earned"]), len(CATALOGUE)),
        )
    )

    if fresh:
        db.commit()

    totals = {tier: {"earned": 0, "total": 0} for tier in TIERS}
    for item in out:
        totals[item["tier"]]["total"] += 1
        if item["earned"]:
            totals[item["tier"]]["earned"] += 1

    return {
        "trophies": out,
        "totals": totals,
        "earned": sum(1 for item in out if item["earned"]),
        "total": len(out),
        "newly_earned": fresh,
    }


def _shape(trophy, facts, row, has, progress_override=None):
    current, target = progress_override or (None, None)
    if progress_override is None and trophy.get("progress"):
        try:
            current, target = trophy["progress"](facts)
        except Exception:
            current, target = None, None

    hidden = trophy["tier"] == HIDDEN
    return {
        "id": trophy["id"],
        "tier": trophy["tier"],
        # Un trofeu ascuns neluat nu-și spune numele — asta e tot rostul lui.
        # Luat, se dezvăluie complet.
        "name": trophy["name"] if (has or not hidden) else "???",
        "description": trophy["description"] if (has or not hidden) else "",
        "hidden": hidden,
        "earned": bool(has),
        "earned_at": serializers.iso_utc(row.earned_at) if row is not None else None,
        "progress": (
            {"current": min(current, target), "target": target}
            if current is not None and target
            else None
        ),
    }


def _enrich(db: Session, user: models.User, facts: dict):
    """Faptele care cer o a doua trecere peste rețetele gătite.

    Ținute separat ca `collect_facts` să rămână o listă de interogări, nu un
    amestec de interogări și reguli.
    """
    from services import ranks

    rows = (
        db.query(models.CookLog, models.Recipe)
        .join(models.Recipe, models.Recipe.id == models.CookLog.recipe_id)
        .filter(models.CookLog.user_id == user.id)
        .all()
    )
    kcals = []
    course_counts = {}
    above_rank = False
    boils = False
    user_tier = ranks.tier_for_xp(user.xp_total or 0)
    for log, recipe in rows:
        if recipe.calories:
            kcals.append(recipe.calories)
        if recipe.course:
            course_counts[recipe.course] = course_counts.get(recipe.course, 0) + 1
        # „Ambitious": la momentul gătirii, rețeta era peste rank-ul tău. Folosim
        # rank-ul copiat în CookLog, nu cel de acum: un moderator care coboară
        # rank-ul unei rețete nu trebuie să-ți ia trofeul.
        if ranks.first_tier_of_rank(log.rank or "copper") > user_tier + 1:
            above_rank = True
        if not boils:
            steps = serializers._load_json(recipe.steps, [])
            for step in steps:
                text = (step.get("text", "") if isinstance(step, dict) else str(step)).lower()
                if ("boil" in text and "water" in text) or "fierbe apa" in text or "apă clocotită" in text:
                    boils = True
                    break

    # Durata estimată a rețetei, per sesiune — „Speed Chef" și „Slow and
    # Steady" compară cronometrul real cu ea.
    estimates = {}
    for session in facts["sessions"]:
        recipe = db.query(models.Recipe).filter(
            models.Recipe.id == session.recipe_id
        ).first()
        if recipe and recipe.duration_min:
            estimates[session.id] = recipe.duration_min
    facts["estimates"] = estimates

    facts["cooked_kcal"] = kcals
    facts["course_counts"] = course_counts
    facts["above_rank_cook"] = above_rank
    facts["boils_water"] = boils


def catalogue_size() -> int:
    return len(CATALOGUE) + 1
