from PyQt5.QtWidgets import QApplication

class ScreenshotHandler:
    def __init__(self, window):
        self.window = window

    def take_screenshot(self, rect):
        """Создание скриншота выделенной области."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.window.winId(), rect.x(), rect.y(), rect.width(), rect.height())
        screenshot.save("screenshot.png")