"""Backend configuration entry points."""

from app.backend.config.api import get_api_settings
from app.backend.config.aster import get_aster_settings
from app.backend.config.database import get_database_settings
from app.backend.config.llm import get_llm_settings
from app.backend.config.twitter import get_twitter_settings
from dotenv import load_dotenv

load_dotenv()

__all__ = [
    "get_api_settings",
    "get_aster_settings",
    "get_database_settings",
    "get_llm_settings",
    "get_twitter_settings",
]
