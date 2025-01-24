from PyQt5.QtWidgets import QMainWindow, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QColor, QPainter, QPen, QPalette
import Quartz.CoreGraphics as CG
from screenshot import ScreenshotHandler
from key_listener import KeyListener
from process import ProcessHandler
from text_parser import TextParser
import os

class Overlay(QMainWindow):
    def __init__(self, target_process_name):
        super().__init__()
        self.target_process_name = target_process_name
        self.process_handler = ProcessHandler(target_process_name)
        self.key_listener = KeyListener(14, CG.kCGEventFlagMaskControl, self.start_selection)
        self.screenshot_handler = ScreenshotHandler(self)  # Передаем self как окно
        self.is_selecting = False
        self.selection_start = None
        self.selection_end = None
        self.overlay_widget = None

        # Создаем экземпляр TextParser
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
        config_path = os.path.join(base_dir, "itemTypes.json")
        self.text_parser = TextParser(config_path)

        self.setWindowTitle("Оверлей для процесса")
        self.setGeometry(100, 100, 300, 100)

        if self.process_handler.is_process_running():
            self.create_overlay()
        else:
            self.show_notification()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start(1000)

        self.key_listener.start_listener()

    def show_notification(self):
        """Показываем уведомление, если процесс не найден."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Процесс {self.target_process_name} не найден.")
        msg.setWindowTitle("Уведомление")
        msg.exec_()

    def create_overlay(self):
        """Создание оверлея, приклеенного к верхней части окна процесса."""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Разрешаем обработку событий мыши
        self.setPalette(QPalette(QColor(255, 0, 0, 0)))  # Прозрачный фон
        self.show()

    def update_overlay_position(self):
        """Обновляем позицию оверлея относительно окна процесса."""
        if hasattr(self.process_handler, 'target_pid'):
            window_info = self.get_window_position()
            if window_info:
                x, y, width, height, top_bar_height = window_info
                overlay_width = width  # Оверлей будет того же размера, что и окно процесса
                overlay_height = height - 30  # Уменьшаем высоту на высоту верхнего бара

                # Приводим координаты и размеры к целым числам
                new_x = int(x)
                new_y = int(y) + 30  # Смещение по высоте на высоту верхнего бара
                new_width = int(overlay_width)
                new_height = int(overlay_height)

                # Перемещаем оверлей в позицию окна процесса
                self.setGeometry(new_x, new_y, new_width, new_height)

    def get_window_position(self):
        """Получаем координаты окна процесса с использованием Quartz."""
        try:
            window_list = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionAll, CG.kCGEventNull)
            for window in window_list:
                if window.get('kCGWindowOwnerPID') == self.process_handler.target_pid:
                    if window.get('kCGWindowName') == "Дистанционная игра":
                        bounds = window.get('kCGWindowBounds')
                        if bounds:
                            # Пытаемся определить высоту верхнего бара
                            top_bar_height = 0
                            if 'kCGWindowTitle' in window:
                                top_bar_height = 30  # Примерная высота верхнего бара (можно настроить)
                            return bounds['X'], bounds['Y'], bounds['Width'], bounds['Height'], top_bar_height
        except Exception as e:
            print(f"Ошибка: {e}")
        return None

    def mousePressEvent(self, event):
        """Начало выделения области для скриншота."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.selection_start = event.pos()
            self.is_selecting = True

    def mouseMoveEvent(self, event):
        """Обновление выделенной области для скриншота."""
        if self.is_selecting and self.selection_start:
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Завершение выделения области и создание скриншота."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            if self.selection_start and self.selection_end:
                self.is_selecting = False
                x1, y1 = self.selection_start.x(), self.selection_start.y()
                x2, y2 = self.selection_end.x(), self.selection_end.y()

                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)

                top += 68  # Смещение для верхнего бара
                bottom += 68

                rect = QRect(left, top, right - left, bottom - top)

                if rect.width() > 0 and rect.height() > 0:
                    # Делаем скриншот и получаем изображение
                    processed_image = self.screenshot_handler.take_screenshot(rect)

                    # Извлекаем текст из изображения
                    extracted_text = self.text_parser.extract_text(processed_image)

                    # Парсим текст и выводим результаты
                    parsed_results = self.text_parser.parse_text(extracted_text)
                    print(f"Parsed results: {parsed_results}")

                    # Показываем извлеченный текст во всплывающем окне
                    self.text_parser.show_text_popup(extracted_text)
                else:
                    print("Invalid selection area, skipping screenshot.")

                self.overlay_widget.close()

    def start_selection(self):
        """Активируем режим выделения области для скриншота."""
        self.is_selecting = True
        self.selection_start = None
        self.selection_end = None
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.1);")  # Темнее
        self.overlay_widget.show()

    def paintEvent(self, event):
        """Отображаем выделенную область для скриншота."""
        if self.is_selecting and self.selection_start and self.selection_end:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
            rect = QRect(self.selection_start, self.selection_end)
            painter.drawRect(rect)

    def keyPressEvent(self, event):
        """Закрытие оверлея при нажатии клавиши Escape."""
        if event.key() == Qt.Key_Escape:
            """Возвращаем оверлей в исходное состояние."""
            self.is_selecting = False
            if self.overlay_widget:
                self.overlay_widget.close()
            self.create_overlay()