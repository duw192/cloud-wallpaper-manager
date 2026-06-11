import ctypes
from pathlib import Path


class WallpaperService:
    """Windows wallpaper service."""

    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02

    @staticmethod
    def set_wallpaper(image_path: str) -> bool:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Wallpaper not found: {image_path}")

        result = ctypes.windll.user32.SystemParametersInfoW(
            WallpaperService.SPI_SETDESKWALLPAPER,
            0,
            str(path),
            WallpaperService.SPIF_UPDATEINIFILE | WallpaperService.SPIF_SENDCHANGE,
        )
        return bool(result)
