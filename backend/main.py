from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import models
from config import settings
from routers import auth, habits, metrics, heart_rate, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    # Seed users
    _seed_users()
    # Start scheduler
    from services.scheduler import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="HealthSync API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173", "https://app.healthsync.online"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(heart_rate.router)
app.include_router(insights.router)


@app.get("/health")
def health():
    return {"status": "ok"}


def _seed_users():
    """Create the two users at startup if they don't exist."""
    from auth import hash_password
    db = SessionLocal()
    try:
        users_data = [
            {
                "username": settings.user1_username,
                "password": settings.user1_password,
                "telegram_id": settings.user1_telegram_id,
                "name": settings.user1_username,
            },
            {
                "username": settings.user2_username,
                "password": settings.user2_password,
                "telegram_id": settings.user2_telegram_id,
                "name": settings.user2_username,
            },
        ]
        for u in users_data:
            existing = db.query(models.User).filter(
                (models.User.username == u["username"]) |
                (models.User.telegram_id == u["telegram_id"])
            ).first()
            if not existing:
                user = models.User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    telegram_id=u["telegram_id"],
                    name=u["name"],
                    settings_json={},
                )
                db.add(user)
            else:
                # Update credentials if username/telegram_id changed
                existing.username = u["username"]
                existing.telegram_id = u["telegram_id"]
                existing.password_hash = hash_password(u["password"])
        db.commit()
    finally:
        db.close()
