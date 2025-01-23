import sys
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QPalette
import Quartz.CoreGraphics as CG

class MainWindow(QMainWindow):
    def __init__(self, target_process_name):
        super().__init__()
        self.target_process_name = target_process_name
        self.setWindowTitle("Оверлей для процесса")
        self.setGeometry(100, 100, 200, 50)

        if self.is_process_running():
            self.create_overlay()
        else:
            self.show_notification()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start(1000)  # 1 секунда

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

                # Центрируем оверлей по горизонтали
                new_x = x + width // 2 - overlay_width // 2
                new_y = y  # Оверлей будет на верхней границе окна

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

def main():
    target_process_name = "RemotePlay"  # Имя процесса
    app = QApplication(sys.argv)
    window = MainWindow(target_process_name)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()