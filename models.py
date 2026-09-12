from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Table, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ---------- USERS & PROFILE (Secțiunea 5) ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, default="")
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    xp_total = Column(Integer, default=0)
    level = Column(Integer, default=1)
    language = Column(String, default="ro")
    theme = Column(String, default="light")
    units = Column(String, default="metric")
    allergies = Column(Text, default="")          # listă simplă, separată prin virgulă
    preferences = Column(Text, default="")
    avatar_url = Column(String, default="")
    cover_url = Column(String, default="")         # imaginea de fundal (cover) a profilului
    bio = Column(Text, default="")
    settings = Column(Text, default="")            # JSON: preferințe client (privacy, notificări, mesaje, 2FA, blocked)
    is_active = Column(Boolean, default=True)      # dezactivat de moderator/admin
    role = Column(String, default="user")          # user / moderator / admin
    suspended_until = Column(DateTime, nullable=True)  # sancțiune temporară (deps.require_not_suspended)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipes = relationship("Recipe", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    posts = relationship("ForumPost", back_populates="author")

# ---------- RECIPES (Secțiunea 1) ----------
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    steps = Column(Text, default="")              # pașii, ca text/JSON
    ingredients = Column(Text, default="")
    nutrition = Column(Text, default="")          # JSON: [{key,label,value,unit,max}]
    allergens = Column(Text, default="")          # JSON: {contains:[], free:[]}
    servings = Column(Integer, default=1)
    origin = Column(String, default="")           # țara de origine (pașaport culinar)
    duration_min = Column(Integer, default=0)
    difficulty = Column(String, default="easy")
    calories = Column(Integer, default=0)
    # Rank-ul rețetei (copper..chef, fără divizii). Înlocuiește easy/medium/hard
    # ca dificultate afișată; `difficulty` rămâne pentru compatibilitate.
    rank = Column(String, default="copper")
    image_url = Column(String, default="")        # poză cover (ImageKit)
    images = Column(Text, default="")             # JSON: listă URL-uri galerie
    moderation_status = Column(String, default="ok")  # ok / flagged / hidden
    ai_notes = Column(Text, default="")           # motivul de la validarea AI
    # Limba în care a scris autorul. Conținutul salvat e tradus în engleză;
    # asta ne lasă să afișăm „Translated from Romanian" pe pagina rețetei.
    source_language = Column(String, default="en")
    is_daily_dish = Column(Boolean, default=False)  # Daily Global Dish
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="recipes")
    reviews = relationship("Review", back_populates="recipe")

# ---------- REVIEWS (Secțiunea 1) ----------
class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, default=5)
    comment = Column(Text, default="")
    photo_url = Column(String, default="")
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    recipe = relationship("Recipe", back_populates="reviews")

# ---------- SAVED RECIPES / COLLECTIONS (Secțiunea 1) ----------
class SavedRecipe(Base):
    __tablename__ = "saved_recipes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    collection_name = Column(String, default="Favorites")
    cooked = Column(Boolean, default=False)       # gătită sau doar salvată
    cooked_verified = Column(Boolean, default=False)  # AI a confirmat poza de gătit
    cook_photo_url = Column(String, default="")   # dovada gătitului (ImageKit)
    cooked_at = Column(DateTime, nullable=True)   # când a fost confirmat gătitul
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------- LEARN (Secțiunea 3) ----------
class Lesson(Base):
    """Un hexagon din fagure. Conținutul vine din `data/lessons_seed.py` și e
    re-scris la fiecare pornire (vezi services.learn.seed_lessons), așa că DB-ul
    e sursa pentru citire, dar fișierul de seed rămâne sursa adevărului —
    excepție fac lecțiile editate din /admin, marcate cu `custom=True`."""
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    branch = Column(String, default="", index=True)   # id-ul ramurii; "root" pentru Foundations
    icon = Column(String, default="")
    video_url = Column(String, default="")            # gol la seed — se completează din /admin
    summary = Column(Text, default="")
    content = Column(Text, default="")                # intro (text lung)
    steps = Column(Text, default="")                  # JSON: listă de pași
    tips = Column(Text, default="")                   # JSON: listă de sfaturi
    quiz = Column(Text, default="")                   # JSON: [{q, options[], correct}]
    mastery_quiz = Column(Text, default="")           # JSON: același format, mai greu
    prereqs = Column(Text, default="")                # JSON: listă de slug-uri
    req_tier = Column(Integer, default=0)             # treapta minimă de rank (0..15)
    est_min = Column(Integer, default=20)
    xp = Column(Integer, default=0)                   # XP la trecerea quiz-ului
    mastery_xp = Column(Integer, default=0)           # XP suplimentar la mastery
    hex_q = Column(Integer, default=0)                # coordonate axiale în fagure
    hex_r = Column(Integer, default=0)
    depth = Column(Integer, default=0)                # poziția în ramură (0 = rădăcină)
    level = Column(String, default="beginner")        # istoric — înlocuit de req_tier
    order = Column(Integer, default=0)
    custom = Column(Boolean, default=False)           # editată din /admin -> seed-ul n-o suprascrie


class LessonProgress(Base):
    """Progresul unui user pe o lecție. Are două niveluri: `completed` (quiz-ul
    de bază trecut) și `mastered`, care cere și quiz-ul avansat, și o rețetă
    gătită confirmată de AI după terminarea lecției."""
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)
    completed = Column(Boolean, default=False)
    quiz_score = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    mastery_passed = Column(Boolean, default=False)   # quiz-ul avansat trecut
    mastered = Column(Boolean, default=False)         # quiz avansat + dish gătit
    mastered_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)
    mastery_attempts = Column(Integer, default=0)
    # Cooldown-ul de 24h după un quiz ratat stă în DB, nu în localStorage: altfel
    # se ocolea golind stocarea browserului.
    cooldown_until = Column(DateTime, nullable=True)
    mastery_cooldown_until = Column(DateTime, nullable=True)


class DailyChallenge(Base):
    """Provocările zilei — 3 rețete alese determinist pentru data respectivă.
    Se completează gătind rețeta și trecând verificarea AI a pozei."""
    __tablename__ = "daily_challenges"
    __table_args__ = (
        UniqueConstraint("date", "slot", name="uq_daily_challenge_slot"),
    )
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)                 # YYYY-MM-DD (UTC)
    slot = Column(Integer, default=0)                 # 0 = easy, 1 = medium, 2 = hard
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    rank = Column(String, default="copper")           # rank-ul rețetei, pentru insignă
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyChallengeDone(Base):
    __tablename__ = "daily_challenge_done"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_daily_challenge_done"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), index=True)
    xp_awarded = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)

# ---------- FORUM (Secțiunea 4) ----------
class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, default="")
    category = Column(String, default="Questions")  # istoric — înlocuit de `tag`
    # Subforumul e limba în care scrii; subiectul îl dă tag-ul.
    language = Column(String, default="en", index=True)
    tag = Column(String, default="question", index=True)
    moderation_status = Column(String, default="ok")  # ok / hidden (moderare)
    votes = Column(Integer, default=0)      # sumă cache-uită a ForumVote
    views = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("ForumComment", back_populates="post")


class ForumVote(Base):
    """Un vot per user per postare (+1 / -1). Contorul `ForumPost.votes` e doar
    o sumă cache-uită — aici e adevărul, ca să știm și cum a votat cel care
    se uită la listă."""
    __tablename__ = "forum_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_forum_vote"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), index=True)
    value = Column(Integer, default=0)      # 1 sau -1
    created_at = Column(DateTime, default=datetime.utcnow)

class ForumComment(Base):
    __tablename__ = "forum_comments"
    id = Column(Integer, primary_key=True, index=True)
    body = Column(Text, default="")
    votes = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)  # threaded
    post_id = Column(Integer, ForeignKey("forum_posts.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ForumPost", back_populates="comments")
    author = relationship("User")

# ---------- BADGES (Secțiunea 5) ----------
class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    icon_url = Column(String, default="")

class UserBadge(Base):
    __tablename__ = "user_badges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_id = Column(Integer, ForeignKey("badges.id"))
    earned_at = Column(DateTime, default=datetime.utcnow)

# ---------- FOLLOW (Secțiunea 7 - urmărire utilizatori) ----------
class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_pair"),
    )
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"))   # cine urmărește
    following_id = Column(Integer, ForeignKey("users.id"))  # cine e urmărit
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------- BLOCĂRI ÎNTRE UTILIZATORI ----------
class Block(Base):
    """Blocarea e unidirecțională ca acțiune, dar simetrică ca efect: dacă A îl
    blochează pe B, niciunul nu mai vede conținutul celuilalt."""
    __tablename__ = "blocks"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
    )
    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), index=True)
    blocked_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- DAILY GLOBAL DISH (Secțiunea 4 - istoric zilnic) ----------
class DailyDish(Base):
    __tablename__ = "daily_dishes"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)  # YYYY-MM-DD (UTC)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- CHAT CU KOOKA ----------
class ChatConversation(Base):
    """Un fir de discuție cu asistentul. Titlul e generat din prima întrebare,
    ca lista din bara laterală să fie recunoscibilă fără să deschizi firul."""
    __tablename__ = "chat_conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class ChatMessage(Base):
    """Un mesaj din fir. `role` e 'user' sau 'ai'.

    Pozele NU se stochează: modelul le vede o dată, ca data-URI efemer, apoi
    rămâne doar `has_photo` ca să putem reda bula corect la reîncărcare.
    `cards` ține JSON-ul atașamentelor bogate (rețete recomandate, estimarea
    nutrițională), ca firul reîncărcat să arate exact ca la prima rulare.
    """
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), index=True)
    role = Column(String, default="user")
    text = Column(Text, default="")
    has_photo = Column(Boolean, default=False)
    cards = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")


# ---------- PLANIFICATOR: lista de cumpărături + calendarul de mese ----------
class ShoppingItem(Base):
    """O linie din lista de cumpărături.

    Stătea în localStorage, deci exista doar în browserul în care ai adăugat-o:
    puneai ingredientele de pe telefon și pe laptop lista era goală. Cantitatea
    e păstrată ca text liber (`quantity` + `unit`) pentru că oamenii scriu „2",
    „500 g" și „o legătură" — a o forța la un număr ar pierde informație.
    """
    __tablename__ = "shopping_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    quantity = Column(String, default="")      # „2", „500", gol = nespecificat
    unit = Column(String, default="")          # „g", „ml", „buc"
    checked = Column(Boolean, default=False)   # bifat în magazin
    # de unde a venit: adăugat manual, dintr-o rețetă, sau cerut din chat
    source = Column(String, default="manual")  # manual | recipe | ai
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MealPlanEntry(Base):
    """O masă planificată într-o zi.

    `recipe_id` e opțional: poți plănui „Ciorbă de la mama", care nu e o rețetă
    din aplicație. Când există, pagina face legătura către rețetă și lista de
    cumpărături poate prelua ingredientele.
    """
    __tablename__ = "meal_plan_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(String, index=True)          # YYYY-MM-DD (ora locală a celui care plănuiește)
    slot = Column(String, default="dinner")    # breakfast | lunch | dinner | snack
    title = Column(String, default="")
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    source = Column(String, default="manual")  # manual | recipe | ai
    position = Column(Integer, default=0)      # ordinea în cadrul zilei
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- RAPORTĂRI ----------
class Report(Base):
    """Un raport trimis de un utilizator despre o rețetă sau o postare.

    Butonul „Report" exista în interfață și nu făcea nimic. Acum ajunge într-o
    coadă pe care moderatorii o văd în consolă. Un singur raport deschis per
    (raportor, obiect) — a apăsa de trei ori nu înseamnă trei semnalări.
    """
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_report_once"),
    )
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), index=True)
    target_type = Column(String, index=True)   # recipe | forum_post | forum_comment
    target_id = Column(Integer, index=True)
    reason = Column(String, default="other")   # cheie fixă, vezi services/reports.py
    details = Column(Text, default="")
    status = Column(String, default="open", index=True)  # open | resolved | dismissed
    handled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    handled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
