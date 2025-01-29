import psutil
import ctypes
import Quartz.CoreGraphics as CG
from AppKit import NSScreen
from Foundation import NSMakeRect

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
        """Получаем разрешение экрана, на котором находится окно процесса."""
        window_pos = self._get_window_position()
        if not window_pos:
            return 0, 0, 0, 0

        x, y, width, height = window_pos

        # Получаем список всех экранов
        screens = NSScreen.screens()
        for screen in screens:
            frame = screen.frame()
            if frame.origin.x <= x <= frame.origin.x + frame.size.width:
               # frame.origin.y <= y <= frame.origin.y + frame.size.height:
                return frame.origin.x, frame.origin.y, frame.size.width, frame.size.height

        return 0, 0, 0, 0

    def _get_window_position(self):
        """Получаем координаты окна процесса и разрешение дисплея, на котором оно находится."""
        if not self.target_pid:
            return None

        # Получаем список всех окон
        window_list = CG.CGWindowListCopyWindowInfo(
            CG.kCGWindowListOptionAll,
            CG.kCGNullWindowID
        )

        for window in window_list:
            # Проверяем, что окно принадлежит нашему процессу
            if window.get('kCGWindowOwnerPID') == self.target_pid:
                bounds = window.get('kCGWindowBounds')
                if bounds:
                    x = bounds.get('X', 0)
                    y = bounds.get('Y', 0)
                    width = bounds.get('Width', 0)
                    height = bounds.get('Height', 0)

                    # Определяем, на каком дисплее находится окно
                    display_id = self._get_display_for_window(x, y, width, height)
                    if display_id:
                        # Получаем разрешение дисплея
                        screen_width, screen_height = self._get_display_resolution(display_id)

                        # Проверка на полноэкранный режим
                        if width >= screen_width and height >= screen_height:
                            print("Окно в полноэкранном режиме")
                            return x, y, screen_width, screen_height

                        return x, y, width, height
        return None

    @staticmethod
    def _get_display_for_window(x, y, width, height):
        """
        Возвращает идентификатор дисплея, на котором находится окно с заданными координатами и размерами.
        """
        # Получаем список всех активных дисплеев
        max_displays = 10
        display_ids = (ctypes.c_uint32 * max_displays)()
        error_code, display_ids_tuple, display_count = CG.CGGetActiveDisplayList(max_displays, display_ids, None)

        # Центр окна
        window_center_x = x + width / 2
        window_center_y = y + height / 2

        # Проверяем, на каком дисплее находится центр окна
        for i in range(display_count):
            display_id = display_ids_tuple[i]
            display_bounds = CG.CGDisplayBounds(display_id)
            if (display_bounds.origin.x <= window_center_x <= display_bounds.origin.x + display_bounds.size.width and
                display_bounds.origin.y <= window_center_y <= display_bounds.origin.y + display_bounds.size.height):
                return display_id  # Возвращаем идентификатор дисплея

        return None  # Если дисплей не найден

    def _get_display_resolution(self, display_id):
        """
        Возвращает разрешение дисплея по его идентификатору.
        """
        bounds = CG.CGDisplayBounds(display_id)
        return bounds.size.width, bounds.size.height