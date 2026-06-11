from PySide6.QtCore import QObject, QTimer, Signal


class SchedulerService(QObject):
    tick = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick.emit)

    def start(self, interval_minutes: int) -> None:
        interval_ms = max(1, interval_minutes) * 60 * 1000
        self.timer.start(interval_ms)

    def stop(self) -> None:
        self.timer.stop()

    def is_running(self) -> bool:
        return self.timer.isActive()
