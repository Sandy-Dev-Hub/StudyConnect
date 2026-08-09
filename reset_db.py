import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("DATABASE_URL")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql+pg8000://", 1)
if url.startswith("postgresql://") and not url.startswith("postgresql+"):
    url = url.replace("postgresql://", "postgresql+pg8000://", 1)

engine = create_engine(url)
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS answers CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS questions CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS user_profiles CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS study_groups CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS study_group_members CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS messages CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS doubts CASCADE;"))
    
print("Cleaned up tables!")
