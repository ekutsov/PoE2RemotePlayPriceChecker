import sys
from typing import Dict, Optional, Tuple

import Quartz.CoreGraphics as CG
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from process_handler import ProcessHandler
from key_listener import KeyListener
from screenshot_handler import ScreenshotHandler
from mouse_tracking_panel import MouseTrackingPanel
from text_editor_overlay import TextEditorOverlay

from logger_config import logger
from parsing_utils import load_ndjson, build_item_lookup, build_stat_lookup, parse_item

class Constants:
    CTRL_E_KEY_CODE = 14
    ESC_KEY_CODE = 53
    CTRL_MASK = CG.kCGEventFlagMaskControl

class Overlay(QMainWindow):
    def __init__(
        self,
        process_handler: ProcessHandler,
        screenshot_handler: ScreenshotHandler,
        items_path: str = "items.ndjson",
        stats_path: str = "stats.ndjson"
    ) -> None:
        super().__init__()
        self.process_handler = process_handler
        self.screenshot_handler = screenshot_handler

        if not self.process_handler.is_process_running():
            logger.info("Процесс не запущен. Выход из приложения.")
            sys.exit(0)

        self.panel: Optional[MouseTrackingPanel] = None

        # Загружаем конфиги
        self.items = load_ndjson(items_path)
        self.stats = load_ndjson(stats_path)

        # Создаём словари для быстрого поиска
        self.item_lookup = build_item_lookup(self.items)
        self.stat_lookup = build_stat_lookup(self.stats)

        # Настраиваем слушатель клавиш (Ctrl+E)
        self.ctrl_e_listener = KeyListener(
            key_code=Constants.CTRL_E_KEY_CODE,
            modifiers=Constants.CTRL_MASK,
            callback=self.start_selection
        )
        self.ctrl_e_listener.start_listener()

        # Настраиваем слушатель клавиш (ESC)
        self.esc_listener = KeyListener(
            key_code=Constants.ESC_KEY_CODE,
            modifiers=None,
            callback=self.finish_selection
        )
        self.esc_listener.start_listener()

        logger.info("Overlay инициализирован.")

    def start_selection(self) -> None:
        """Создаёт панель MouseTrackingPanel при нажатии Ctrl+E."""
        if self.panel is not None:
            logger.debug("Панель уже активна. Игнорирование запроса на создание новой панели.")
            return

        window_info = self.process_handler.get_screen_resolution()
        if not window_info:
            logger.error("Не удалось получить информацию о разрешении экрана.")
            return

        x, y, width, height = window_info
        rect = ((x, y), (width, height))

        self.panel = MouseTrackingPanel.create_panel(
            rect=rect,
            screenshot_handler=self.screenshot_handler,
            overlay=self
        )
        self.panel.makeKeyAndOrderFront_(None)
        logger.info("Панель выбора создана и отображена.")

    def finish_selection(self, text: str) -> None:
        """
        Закрывает панель (если она есть) и инициирует отображение текстового редактора.

        :param text: Текст, полученный из панели.
        """
        if not self.panel:
            logger.warning("Попытка закрыть несуществующую панель.")
            return

        self.panel.close()
        self.panel = None
        logger.info("Панель выбора закрыта.")
        self.show_text_editor(text)

    def show_text_editor(self, text: str) -> None:
        """
        Отображает TextEditorOverlay для редактирования типа предмета.

        :param text: Текст для редактирования.
        """
        if self.panel is not None:
            logger.debug("Панель уже активна. Игнорирование запроса на открытие текстового редактора.")
            return

        item = parse_item(text, self.item_lookup, self.stat_lookup)
        if not item:
            logger.warning("Не удалось извлечь тип предмета из текста.")
            return

        self.panel = TextEditorOverlay.create_panel(
            item,
            on_save_callback=self.save_edited_text,
            on_close_callback=self.close_text_editor
        )
        self.panel.makeKeyAndOrderFront_(None)
        logger.info("Текстовый редактор отображён для редактирования типа предмета.")

    def close_text_editor(self) -> None:
        """Callback для закрытия текстового окна."""
        if not self.panel:
            logger.warning("Попытка закрыть несуществующее текстовое окно.")
            return

        self.panel.close()
        self.panel = None
        logger.info("Текстовое окно закрыто.")

    def save_edited_text(self, edited_text: str) -> None:
        """
        Callback для сохранённого текста.

        :param edited_text: Отредактированный текст.
        """
        if not self.panel:
            logger.warning("Попытка сохранить текст без активного текстового окна.")
            return

        self.panel.close()
        self.panel = None
        logger.info(f"Отредактированный текст: {edited_text}")
        # Здесь можно добавить логику сохранения или обработки отредактированного текста

    def closeEvent(self, event) -> None:
        """Обработчик события закрытия окна. Останавливает слушатели клавиш."""
        logger.info("Закрытие Overlay. Остановка слушателей клавиш.")
        self.ctrl_e_listener.stop_listener()
        self.esc_listener.stop_listener()
        if self.panel:
            self.panel.close()
        event.accept()