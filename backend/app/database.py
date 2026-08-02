import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://erp_user:erp_pass@db:5432/erp_consinco",
)

# Provedores de nuvem (Railway, Render, Heroku etc.) costumam fornecer a
# variável DATABASE_URL no formato "postgres://..." ou "postgresql://...",
# sem o driver. O SQLAlchemy exige o driver explícito (+psycopg2).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def garantir_schema():
    """Cria o schema 'erp' no banco caso ainda não exista (necessário em
    bancos novos, como um projeto recém-criado no Supabase)."""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS erp"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
