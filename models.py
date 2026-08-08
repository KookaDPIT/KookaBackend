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
    bio = Column(Text, default="")
    is_active = Column(Boolean, default=True)      # dezactivat de moderator/admin
    role = Column(String, default="user")          # user / moderator / admin
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
    image_url = Column(String, default="")        # poză cover (ImageKit)
    images = Column(Text, default="")             # JSON: listă URL-uri galerie
    moderation_status = Column(String, default="ok")  # ok / flagged / hidden
    ai_notes = Column(Text, default="")           # motivul de la validarea AI
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
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------- LEARN (Secțiunea 3) ----------
class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    video_url = Column(String, default="")
    content = Column(Text, default="")
    level = Column(String, default="beginner")    # beginner -> master_chef
    order = Column(Integer, default=0)            # poziția în skill tree

class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    completed = Column(Boolean, default=False)
    quiz_score = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)

# ---------- FORUM (Secțiunea 4) ----------
class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, default="")
    category = Column(String, default="Questions")  # Questions/Recipes/Tips/Showcase
    votes = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("ForumComment", back_populates="post")

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

# ---------- DAILY GLOBAL DISH (Secțiunea 4 - istoric zilnic) ----------
class DailyDish(Base):
    __tablename__ = "daily_dishes"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)  # YYYY-MM-DD (UTC)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    created_at = Column(DateTime, default=datetime.utcnow)