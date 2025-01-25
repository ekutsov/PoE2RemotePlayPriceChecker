import os
import sys

import Quartz.CoreGraphics as CG
from PyQt5.QtWidgets import QMainWindow

from process_handler import ProcessHandler
from key_listener import KeyListener
from screenshot_handler import ScreenshotHandler

from mouse_tracking_panel import MouseTrackingPanel


class Overlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process_handler = ProcessHandler()
        if not self.process_handler.is_process_running():
            sys.exit(0)

        self.screenshot_handler = ScreenshotHandler()
        self.panel = None

        # Настраиваем listner клавиш (Ctrl+E)
        self.ctrl_e_listener = KeyListener(14, CG.kCGEventFlagMaskControl, self.start_selection)
        self.ctrl_e_listener.start_listener()

        # Настраиваем listner клавиш (ESC)
        self.esc_listener = KeyListener(53, None, self.finish_selection)
        self.esc_listener.start_listener()
        
    def start_selection(self):
        """Создаёт panel (MouseTrackingPanel) при нажатии Ctrl+E."""
        if self.panel is not None:
            return

        window_info = self.process_handler.get_screen_resolution()
        if window_info:
            x, y, width, height = window_info
            rect = ((x, y), (width, height))

            # Создаём панель и передаём self (Overlay), а также self.screenshot_handler
            self.panel = MouseTrackingPanel.create_panel(
                rect,
                screenshot_handler=self.screenshot_handler,
                overlay=self
            )
            self.panel.makeKeyAndOrderFront_(None)

    def finish_selection(self):
        """
        Закрывает панель (если она есть) и ставит self.panel = None.
        """
        if self.panel:
            self.panel.close()
            self.panel = None