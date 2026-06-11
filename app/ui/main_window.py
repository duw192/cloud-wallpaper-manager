from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFileDialog, QMessageBox, QLineEdit, QTextEdit, QGroupBox,
    QFormLayout
)

from app.config import (
    APP_NAME, CACHE_DIR, DEFAULT_INTERVAL_MINUTES, DEFAULT_BATCH_SIZE,
    DEFAULT_MIN_UNUSED_IMAGES, DEFAULT_MAX_CACHE_MB
)
from app.db.database import Database
from app.services.cache_service import CacheService
from app.services.drive_service import DriveService
from app.services.scheduler_service import SchedulerService
from app.services.wallpaper_service import WallpaperService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(720, 560)

        self.db = Database()
        self.cache_service = CacheService(self.db)
        self.drive_service = DriveService(self.db)
        self.scheduler = SchedulerService()
        self.scheduler.tick.connect(self.change_wallpaper)

        self._build_ui()
        self.refresh_stats()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)

        config_group = QGroupBox("Configuration")
        config_form = QFormLayout(config_group)

        self.folder_id_input = QLineEdit()
        self.folder_id_input.setPlaceholderText("Google Drive folder ID")

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(DEFAULT_INTERVAL_MINUTES)
        self.interval_spin.setSuffix(" minutes")

        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 200)
        self.batch_spin.setValue(DEFAULT_BATCH_SIZE)

        self.min_unused_spin = QSpinBox()
        self.min_unused_spin.setRange(0, 200)
        self.min_unused_spin.setValue(DEFAULT_MIN_UNUSED_IMAGES)

        self.max_cache_spin = QSpinBox()
        self.max_cache_spin.setRange(50, 100000)
        self.max_cache_spin.setValue(DEFAULT_MAX_CACHE_MB)
        self.max_cache_spin.setSuffix(" MB")

        config_form.addRow("Drive folder ID:", self.folder_id_input)
        config_form.addRow("Change interval:", self.interval_spin)
        config_form.addRow("Download batch size:", self.batch_spin)
        config_form.addRow("Min unused images:", self.min_unused_spin)
        config_form.addRow("Max cache size:", self.max_cache_spin)
        layout.addWidget(config_group)

        button_row = QHBoxLayout()
        self.import_button = QPushButton("Import local images")
        self.download_button = QPushButton("Download from Drive")
        self.change_now_button = QPushButton("Change now")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        self.import_button.clicked.connect(self.import_local_images)
        self.download_button.clicked.connect(self.download_from_drive)
        self.change_now_button.clicked.connect(self.change_wallpaper)
        self.start_button.clicked.connect(self.start_scheduler)
        self.stop_button.clicked.connect(self.stop_scheduler)

        for btn in [self.import_button, self.download_button, self.change_now_button, self.start_button, self.stop_button]:
            button_row.addWidget(btn)
        layout.addLayout(button_row)

        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.setCentralWidget(root)

    def log(self, message: str):
        self.log_box.append(message)

    def refresh_stats(self):
        total = self.db.count_all()
        unused = self.db.count_unused()
        cache_mb = self.db.total_cache_bytes() / 1024 / 1024
        status = "running" if self.scheduler.is_running() else "stopped"
        self.stats_label.setText(
            f"Cache folder: {CACHE_DIR}\n"
            f"Images: {total} | Unused: {unused} | Cache: {cache_mb:.2f} MB | Scheduler: {status}"
        )

    def import_local_images(self):
        folder = QFileDialog.getExistingDirectory(self, "Select local wallpaper folder")
        if not folder:
            return
        try:
            count = self.cache_service.import_local_images(folder)
            self.log(f"Imported {count} local images.")
            self.cleanup_cache()
            self.refresh_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Import error", str(exc))

    def download_from_drive(self):
        folder_id = self.folder_id_input.text().strip()
        if not folder_id:
            QMessageBox.warning(self, "Missing folder ID", "Please enter your Google Drive folder ID.")
            return
        try:
            count = self.drive_service.download_images(
                folder_id=folder_id,
                cache_dir=Path(CACHE_DIR),
                batch_size=self.batch_spin.value(),
            )
            self.log(f"Downloaded {count} images from Google Drive.")
            self.cleanup_cache()
            self.refresh_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Drive error", str(exc))

    def ensure_enough_images(self):
        if self.db.count_unused() > self.min_unused_spin.value():
            return

        folder_id = self.folder_id_input.text().strip()
        if not folder_id:
            return

        try:
            count = self.drive_service.download_images(
                folder_id=folder_id,
                cache_dir=Path(CACHE_DIR),
                batch_size=self.batch_spin.value(),
            )
            if count:
                self.log(f"Auto-downloaded {count} images because unused cache was low.")
        except Exception as exc:
            self.log(f"Offline or Drive error. Using cached images only. Detail: {exc}")

    def change_wallpaper(self):
        try:
            self.ensure_enough_images()
            row = self.db.get_next_wallpaper()
            if not row:
                self.log("No cached wallpaper available.")
                self.refresh_stats()
                return

            ok = WallpaperService.set_wallpaper(row["local_path"])
            if ok:
                self.db.mark_used(row["id"])
                self.log(f"Changed wallpaper: {row['file_name']}")
            else:
                self.log(f"Windows refused to set wallpaper: {row['file_name']}")

            self.cleanup_cache()
            self.refresh_stats()
        except Exception as exc:
            self.log(f"Change wallpaper error: {exc}")
            self.refresh_stats()

    def cleanup_cache(self):
        deleted = self.cache_service.cleanup_if_needed(self.max_cache_spin.value())
        if deleted:
            self.log(f"Cleaned up {deleted} old used images.")

    def start_scheduler(self):
        self.scheduler.start(self.interval_spin.value())
        self.log(f"Scheduler started. Interval: {self.interval_spin.value()} minutes.")
        self.refresh_stats()

    def stop_scheduler(self):
        self.scheduler.stop()
        self.log("Scheduler stopped.")
        self.refresh_stats()

    def closeEvent(self, event):
        self.db.close()
        event.accept()
