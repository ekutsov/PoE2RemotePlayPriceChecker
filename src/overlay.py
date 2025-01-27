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

class Overlay(QMainWindow):
    # Загружаем конфиги
    items = load_ndjson("items.ndjson")
    stats = load_ndjson("stats.ndjson")

    # Создаём словари для быстрого поиска
    item_lookup = build_item_lookup(items)
    stat_lookup = build_stat_lookup(stats)

    # Константы для кодов клавиш
    CTRL_E_KEY_CODE = 14
    ESC_KEY_CODE = 53
    CTRL_MASK = CG.kCGEventFlagMaskControl

    def __init__(self) -> None:
        super().__init__()
        self.process_handler: ProcessHandler = ProcessHandler()

        if not self.process_handler.is_process_running():
            logger.info("Процесс не запущен. Выход из приложения.")
            sys.exit(0)

        self.screenshot_handler: ScreenshotHandler = ScreenshotHandler()
        self.panel: Optional[MouseTrackingPanel] = None

        # Настраиваем слушатель клавиш (Ctrl+E)
        self.ctrl_e_listener: KeyListener = KeyListener(
            key_code=self.CTRL_E_KEY_CODE,
            modifiers=self.CTRL_MASK,
            callback=self.start_selection
        )
        self.ctrl_e_listener.start_listener()

        # Настраиваем слушатель клавиш (ESC)
        self.esc_listener: KeyListener = KeyListener(
            key_code=self.ESC_KEY_CODE,
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

        window_info: Optional[Tuple[int, int, int, int]] = self.process_handler.get_screen_resolution()
        if window_info:
            x, y, width, height = window_info
            rect: Tuple[Tuple[int, int], Tuple[int, int]] = ((x, y), (width, height))

            # Создаём панель и передаём self (Overlay), а также self.screenshot_handler
            self.panel = MouseTrackingPanel.create_panel(
                rect=rect,
                screenshot_handler=self.screenshot_handler,
                overlay=self
            )
            self.panel.makeKeyAndOrderFront_(None)
            logger.info("Панель выбора создана и отображена.")
        else:
            logger.error("Не удалось получить информацию о разрешении экрана.")

    def finish_selection(self, text: str) -> None:
        """
        Закрывает панель (если она есть) и инициирует отображение текстового редактора.

        :param text: Текст, полученный из панели.
        """
        if self.panel:
            self.panel.close()
            self.panel = None
            logger.info("Панель выбора закрыта.")
            self.show_text_editor(text)
        else:
            logger.warning("Попытка закрыть несуществующую панель.")

    def show_text_editor(self, text: str) -> None:
        """
        Отображает TextEditorOverlay для редактирования типа предмета.

        :param text: Текст для редактирования.
        """
        if self.panel is not None:
            logger.debug("Панель уже активна. Игнорирование запроса на открытие текстового редактора.")
            return

        # Извлекаем тип предмета из текста
        item: str = parse_item(text, self.item_lookup, self.stat_lookup)
        if not item:
            logger.warning("Не удалось извлечь тип предмета из текста.")
            return  # Или обработайте этот случай иначе

        # Создаём TextEditorOverlay с типом предмета
        self.panel = TextEditorOverlay.create_panel(
            item,
            on_save_callback=self.save_edited_text,
            on_close_callback=self.close_text_editor
        )
        self.panel.makeKeyAndOrderFront_(None)
        logger.info("Текстовый редактор отображён для редактирования типа предмета.")

    def close_text_editor(self) -> None:
        """Callback для закрытия текстового окна."""
        if self.panel:
            self.panel.close()
            self.panel = None
            logger.info("Текстовое окно закрыто.")
        else:
            logger.warning("Попытка закрыть несуществующее текстовое окно.")

    def save_edited_text(self, edited_text: str) -> None:
        """
        Callback для сохранённого текста.

        :param edited_text: Отредактированный текст.
        """
        if self.panel:
            self.panel.close()
            self.panel = None
            logger.info(f"Отредактированный текст: {edited_text}")
            # Здесь можно добавить логику сохранения или обработки отредактированного текста
        else:
            logger.warning("Попытка сохранить текст без активного текстового окна.")

    def closeEvent(self, event) -> None:
        """Обработчик события закрытия окна. Останавливает слушатели клавиш."""
        logger.info("Закрытие Overlay. Остановка слушателей клавиш.")
        self.ctrl_e_listener.stop_listener()
        self.esc_listener.stop_listener()
        if self.panel:
            self.panel.close()
        event.accept()