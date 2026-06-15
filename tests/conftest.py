import os

# Set dummy env vars before any bot modules are imported
os.environ.setdefault("BOT_TOKEN", "0000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
os.environ.setdefault("TELEGRAM_API_ID", "12345678")
os.environ.setdefault("TELEGRAM_API_HASH", "aaaabbbbccccddddeeeeffffaaaabbbb")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://bot:bot@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GENIUS_TOKEN", "test_genius_token")
os.environ.setdefault("ADMIN_IDS", "123456789")
os.environ.setdefault("DOWNLOAD_DIR", "/tmp")
