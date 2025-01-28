import sys
import logging
from typing import Any

from PyQt5.QtWidgets import QApplication
from overlay import Overlay
from logger_config import logger, handle_exception
from process_handler import ProcessHandler
from screenshot_handler import ScreenshotHandler


def main() -> None:
    sys.excepthook = handle_exception

    try:
        app = QApplication(sys.argv)

        process_handler = ProcessHandler()
        screenshot_handler = ScreenshotHandler()
        overlay = Overlay(process_handler, screenshot_handler)
        overlay.show()

        logger.info("Приложение запущено.")

        # Используем app.exec() вместо app.exec_(), так как exec_() устарел
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("Необработанное исключение в основном цикле приложения: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()