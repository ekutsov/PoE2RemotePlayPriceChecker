import sys
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QColor, QPalette, QPainter, QPen
import Quartz.CoreGraphics as CG


class MainWindow(QMainWindow):
    def __init__(self, target_process_name):
        super().__init__()
        self.target_process_name = target_process_name
        self.setWindowTitle("Оверлей для процесса")
        self.setGeometry(100, 100, 300, 100)

        self.is_selecting = False
        self.selection_start = None
        self.selection_end = None

        if self.is_process_running():
            self.create_overlay()
        else:
            self.show_notification()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start(1000)

        self.start_global_key_listener()

    def is_process_running(self):
        """Проверка, запущен ли процесс с данным именем."""
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] == self.target_process_name:
                self.target_pid = proc.info['pid']
                return True
        return False

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
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(255, 0, 0, 255))  # Красный фон
        self.setPalette(palette)
        self.show()

    def update_overlay_position(self):
        """Обновляем позицию оверлея относительно окна процесса."""
        if hasattr(self, 'target_pid'):
            window_info = self.get_window_position()
            if window_info:
                x, y, width, height = window_info
                overlay_width = self.width()
                overlay_height = self.height()

                new_x = x + width // 2 - overlay_width // 2
                new_y = y

                self.move(int(new_x), int(new_y))

    def get_window_position(self):
        """Получаем координаты окна процесса с использованием Quartz."""
        try:
            window_list = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionAll, CG.kCGEventNull)
            for window in window_list:
                if window.get('kCGWindowOwnerPID') == self.target_pid and window.get('kCGWindowName') == "Дистанционная игра":
                    bounds = window.get('kCGWindowBounds')
                    if bounds:
                        return bounds['X'], bounds['Y'], bounds['Width'], bounds['Height']
        except Exception as e:
            print(f"Ошибка: {e}")
        return None

    def start_global_key_listener(self):
        """Запуск глобального слушателя клавиш."""
        def global_key_event_callback(proxy, event_type, event, refcon):
            """Обработка глобальных нажатий клавиш."""
            if event_type == CG.kCGEventKeyDown:
                key_code = CG.CGEventGetIntegerValueField(event, CG.kCGKeyboardEventKeycode)
                is_ctrl_pressed = CG.CGEventGetFlags(event) & CG.kCGEventFlagMaskControl

                # Ctrl + E
                if key_code == 14:  # Код клавиши 'E'
                    print("Нажата комбинация Ctrl + E")
                    self.start_selection()
            return event

        event_mask = (1 << CG.kCGEventKeyDown) | (1 << CG.kCGEventKeyUp)

        # Создаем глобальный обработчик событий
        self.event_tap = CG.CGEventTapCreate(
            CG.kCGSessionEventTap,
            CG.kCGHeadInsertEventTap,
            CG.kCGEventTapOptionDefault,
            event_mask,
            global_key_event_callback,
            None,
        )

        if not self.event_tap:
            print("Не удалось создать обработчик событий. Проверьте разрешения.")
            sys.exit(1)

        # Включаем обработчик событий
        CG.CGEventTapEnable(self.event_tap, True)

        # Запускаем цикл событий
        run_loop_source = CG.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
        CG.CFRunLoopAddSource(CG.CFRunLoopGetCurrent(), run_loop_source, CG.kCFRunLoopDefaultMode)

        # Проверяем статус обработчика каждые 2 секунды
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_event_tap_status)
        self.timer.start(2000)

        print("Глобальный обработчик клавиш запущен.")

    def check_event_tap_status(self):
        """Проверяем, активен ли обработчик событий."""
        if not CG.CGEventTapIsEnabled(self.event_tap):
            print("Обработчик событий отключен. Перезапускаем...")
            CG.CGEventTapEnable(self.event_tap, True)

    def start_selection(self):
        """Активируем режим выделения области для скриншота."""
        self.is_selecting = True
        self.selection_start = None
        self.selection_end = None
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.overlay_widget.show()

    def mousePressEvent(self, event):
        """Начало выделения области для скриншота."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.selection_start = event.pos()

    def mouseMoveEvent(self, event):
        """Обновление выделенной области для скриншота."""
        if self.is_selecting and self.selection_start:
            self.selection_end = event.pos()
            self.update_selection_rectangle()

    def mouseReleaseEvent(self, event):
        """Завершение выделения области и создание скриншота."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.take_screenshot()
            self.overlay_widget.close()

    def update_selection_rectangle(self):
        """Обновляем прямоугольник выделенной области."""
        self.update()

    def paintEvent(self, event):
        """Отображаем выделенную область для скриншота."""
        if self.is_selecting and self.selection_start and self.selection_end:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.green, 2, Qt.DashLine))
            rect = QRect(self.selection_start, self.selection_end)
            painter.drawRect(rect)

    def take_screenshot(self):
        """Создание скриншота выделенной области."""
        if self.selection_start and self.selection_end:
            rect = QRect(self.selection_start, self.selection_end)
            print(f"Скриншот области: {rect}")
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId(), rect.x(), rect.y(), rect.width(), rect.height())
            screenshot.save("screenshot.png")
            print("Скриншот сохранен как screenshot.png")


def main():
    target_process_name = "RemotePlay"  # Имя процесса
    app = QApplication(sys.argv)
    window = MainWindow(target_process_name)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()