from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Connection pooling configuration
# SQLite doesn't support pooling, so we only apply to other databases
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
    )
else:
    # PostgreSQL/MySQL connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,           # Number of connections to keep open
        max_overflow=10,       # Additional connections when pool is exhausted
        pool_timeout=30,       # Seconds to wait for a connection
        pool_recycle=1800,     # Recycle connections after 30 minutes
        pool_pre_ping=True,    # Verify connections before using
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()