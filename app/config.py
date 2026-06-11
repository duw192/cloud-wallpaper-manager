from pathlib import Path

APP_NAME = "Cloud Wallpaper Cache Manager"
BASE_DIR = Path.home() / ".cloud_wallpaper_cache_manager"
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = BASE_DIR / "wallpapers.db"
CREDENTIALS_PATH = Path.cwd() / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

DEFAULT_INTERVAL_MINUTES = 30
DEFAULT_BATCH_SIZE = 10
DEFAULT_MIN_UNUSED_IMAGES = 3
DEFAULT_MAX_CACHE_MB = 500
