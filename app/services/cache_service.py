import shutil
from pathlib import Path

from app.config import CACHE_DIR, SUPPORTED_EXTENSIONS
from app.db.database import Database


class CacheService:
    def __init__(self, db: Database, cache_dir: Path = CACHE_DIR):
        self.db = db
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def import_local_images(self, source_folder: str) -> int:
        source = Path(source_folder)
        if not source.exists() or not source.is_dir():
            raise NotADirectoryError(f"Invalid folder: {source_folder}")

        imported = 0
        for file in source.iterdir():
            if not file.is_file():
                continue
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            target = self._unique_target_path(file.name)
            shutil.copy2(file, target)
            self.db.add_wallpaper(
                file_name=target.name,
                local_path=str(target),
                file_size_bytes=target.stat().st_size,
                drive_file_id=None,
            )
            imported += 1
        return imported

    def cleanup_if_needed(self, max_cache_mb: int, cleanup_to_ratio: float = 0.8) -> int:
        max_bytes = max_cache_mb * 1024 * 1024
        target_bytes = int(max_bytes * cleanup_to_ratio)

        if self.db.total_cache_bytes() <= max_bytes:
            return 0

        deleted = 0
        for row in self.db.get_old_used_wallpapers():
            if self.db.total_cache_bytes() <= target_bytes:
                break

            path = Path(row["local_path"])
            if path.exists():
                path.unlink()
            self.db.delete_wallpaper(row["id"])
            deleted += 1

        return deleted

    def _unique_target_path(self, file_name: str) -> Path:
        target = self.cache_dir / file_name
        if not target.exists():
            return target

        stem = target.stem
        suffix = target.suffix
        counter = 1
        while True:
            candidate = self.cache_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
