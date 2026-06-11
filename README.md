# Cloud Wallpaper Cache Manager

A small Windows desktop app that downloads wallpapers from a cloud source, stores them in a local cache, rotates the desktop wallpaper, and keeps working offline.

## Tech Stack

- Python
- PySide6 for desktop UI
- SQLite for local metadata
- Windows API via ctypes for changing wallpaper
- Optional Google Drive API integration

## Features

- Local cache folder management
- SQLite metadata for downloaded/used wallpapers
- Change wallpaper every N minutes
- Prefer unused images before reusing old images
- Cache cleanup by max size
- Offline fallback using cached images
- Optional Google Drive download service scaffold

## Project Structure

```text
cloud_wallpaper_cache_manager/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ db/
│  │  └─ database.py
│  ├─ services/
│  │  ├─ wallpaper_service.py
│  │  ├─ cache_service.py
│  │  ├─ drive_service.py
│  │  └─ scheduler_service.py
│  └─ ui/
│     └─ main_window.py
├─ requirements.txt
└─ README.md
```

## Run

```bash
pip install -r requirements.txt
python -m app.main
```

## Google Drive setup

1. Create Google Cloud OAuth credentials for a desktop app.
2. Download the file as `credentials.json`.
3. Put it in the project root.
4. Put your Google Drive folder ID into the UI field.

The app still works without Google Drive if you import images manually into the cache folder.

## Notes

This is intended as a local personal utility and GitHub portfolio project, not a commercial wallpaper product.
