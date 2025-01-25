import psutil
import Quartz.CoreGraphics as CG
from AppKit import NSScreen

class ProcessHandler:
    def __init__(self, target_process_name="RemotePlay"):
        self.target_process_name = target_process_name
        self.target_pid = self._find_process_pid()

    def _find_process_pid(self):
        """Ищем PID процесса по имени."""
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] == self.target_process_name:
                return proc.info['pid']
        return None

    def is_process_running(self):
        """Проверяем, запущен ли процесс."""
        return self.target_pid is not None

    def get_screen_resolution(self):
        """Получаем координаты окна процесса."""
        main_screen = NSScreen.mainScreen()
        if main_screen:
            frame = main_screen.frame()
            return frame.origin.x, frame.origin.y, frame.size.width, frame.size.height
        return 0, 0, 0, 0