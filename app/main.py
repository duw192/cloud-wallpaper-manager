import sys
from PySide6.QtWidgets import QApplication

from app.config import BASE_DIR, CACHE_DIR
from app.ui.main_window import MainWindow


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
