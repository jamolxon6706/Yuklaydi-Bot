"""arq worker entrypoint."""
from bot.config import settings
from bot.logger import setup_logging
from bot.worker.tasks import WorkerSettings

setup_logging()
WorkerSettings.set_redis(settings.redis_url)
