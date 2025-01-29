import sys
import logging
from typing import Any

from PyQt5.QtWidgets import QApplication
from overlay import Overlay
from logger_config import logger, handle_exception
from process_handler import ProcessHandler
from screenshot_handler import ScreenshotHandler

import rumps  # Импортируем библиотеку для работы с треем macOS


class PoE2PriceChecker(rumps.App):
    def __init__(self, qt_app, overlay):
        super(PoE2PriceChecker, self).__init__("PoE 2 Price Checker", icon="icon.png")  # Укажите путь к иконке
        self.qt_app = qt_app
        self.overlay = overlay
        self.menu = ["Показать Overlay", "Скрыть Overlay"]

    @rumps.clicked("Показать Overlay")
    def show_overlay(self, _):
        self.overlay.show()
        rumps.notification("PoE 2 Price Checker", "Уведомление", "Overlay показан!")

    @rumps.clicked("Скрыть Overlay")
    def hide_overlay(self, _):
        self.overlay.hide()
        rumps.notification("PoE 2 Price Checker", "Уведомление", "Overlay скрыт!")


def main() -> None:
    sys.excepthook = handle_exception

    try:
        qt_app = QApplication(sys.argv)

        process_handler = ProcessHandler()
        screenshot_handler = ScreenshotHandler()
        overlay = Overlay(process_handler, screenshot_handler)

        # Создаем приложение для трея
        tray_app = PoE2PriceChecker(qt_app, overlay)

        logger.info("Приложение запущено.")

        # Запускаем оба приложения
        tray_app.run()  # Запуск приложения в трее
        overlay.show()  # Показываем Overlay при старте

        # Используем app.exec() вместо app.exec_(), так как exec_() устарел
        sys.exit(qt_app.exec())
    except Exception as e:
        logger.exception("Необработанное исключение в основном цикле приложения: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()