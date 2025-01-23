import sys
import psutil
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QPalette
import Quartz.CoreGraphics as CG

# Создаем класс MainWindow
class MainWindow(QMainWindow):
    def __init__(self, target_process_name):
        super().__init__()
        self.target_process_name = target_process_name
        self.setWindowTitle("Пример оверлея для процесса")
        self.setGeometry(100, 100, 800, 600)
        # Проверка, запущен ли процесс
        if self.is_process_running(self.target_process_name):
            print(f"Процесс {self.target_process_name} найден. Создаем оверлей.")
            self.create_overlay()
        else:
            print(f"Процесс {self.target_process_name} не найден.")
            self.show_notification()

        # Таймер для обновления позиции оверлея
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start(100)  # Обновлять каждую 1/10 секунды

    def is_process_running(self, process_name):
        """Проверка, запущен ли процесс с данным именем."""
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] == process_name:
                self.target_pid = proc.info['pid']
                return True
        return False

    def show_notification(self):
        """Показываем всплывающее окно, если процесс не найден."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Процесс {self.target_process_name} не найден.")
        msg.setWindowTitle("Уведомление")
        msg.exec_()

    def create_overlay(self):
        """Создание маленького оверлея, приклеенного к верхней части окна процесса."""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Установим окно прозрачным
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(255, 0, 0, 255))  # Яркий красный фон
        self.setPalette(palette)

        # Создаем маленькое окно
        self.setGeometry(100, 100, 200, 50)  # Маленькое окно
        self.setWindowTitle("Оверлей")

        # Сделаем окно перемещаемым
        self.setMouseTracking(True)
        self.is_dragging = False
        self.drag_position = QPoint(0, 0)

        self.show()

    def update_overlay_position(self):
        """Обновляем позицию оверлея относительно окна процесса."""
        if hasattr(self, 'target_pid') and self.target_pid:
            # Получаем координаты окна процесса с использованием Quartz
            window_info = self.get_window_position(self.target_pid)
            if window_info:
                x, y = window_info
                print(f"Окно процесса перемещено: X={x}, Y={y}")  # Выводим в консоль
                self.move(int(x), int(y - self.height()))   # Приклеиваем оверлей к верхней части окна процесса
            else:
                print(f"Не удалось получить позицию окна для процесса {self.target_pid}")

    def get_window_position(self, pid):
        """Получаем координаты окна процесса с использованием Quartz."""
        try:
            # Получаем все окна на экране
            window_list = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionAll, CG.kCGEventNull)
        
            # Перебираем окна
            for window in window_list:
                window_pid = window.get('kCGWindowOwnerPID')
                window_name = window.get('kCGWindowName', '')

                # Проверяем, что это окно нужного процесса и оно соответствует названию "Дистанционная игра"
                if window_pid == pid and window_name == "Дистанционная игра":
                    # Получаем позицию окна
                    bounds = window.get('kCGWindowBounds')
                    if bounds:
                        # Координаты (x, y) находятся в bounds
                        x = bounds['X']
                        y = bounds['Y']
                        width = bounds['Width']
                        height = bounds['Height']
                        print(f"Окно процесса: X={x}, Y={y}, Width={width}, Height={height}")
                        return x, y  # Возвращаем только координаты
        except Exception as e:
            print(f"Ошибка при получении позиции окна: {e}")
        return None

    def mousePressEvent(self, event):
        """Начало перетаскивания окна."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        """Перетаскивание окна."""
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """Окончание перетаскивания окна."""
        self.is_dragging = False

def main():
    target_process_name = "RemotePlay"  # Замените на имя нужного процесса
    app = QApplication(sys.argv)
    window = MainWindow(target_process_name)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()