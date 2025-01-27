import Quartz.CoreGraphics as CG
from logger_config import logger


class KeyListener:
    def __init__(self, key_code, modifiers=None, callback=None):
        """
        Инициализация слушателя клавиш.

        :param key_code: Код клавиши (например, 14 для 'E').
        :param modifiers: Модификаторы клавиш (например, CG.kCGEventFlagMaskControl для Ctrl). Если None, модификаторы не проверяются.
        :param callback: Callback, вызываемый при нажатии комбинации клавиш.
        """
        if not callable(callback):
            raise ValueError("callback должен быть функцией.")
        self.key_code = key_code
        self.modifiers = modifiers
        self.callback = callback
        self.event_tap = None
        self.run_loop_source = None

    def _key_event_callback(self, proxy, event_type, event, refcon):
        """
        Внутренний обработчик событий нажатия клавиш.

        :param proxy: Прокси для событий.
        :param event_type: Тип события (нажатие или отпускание клавиши).
        :param event: Событие нажатия клавиши.
        :param refcon: Дополнительная информация.
        :return: Событие для дальнейшей обработки.
        """
        if event_type == CG.kCGEventKeyDown:
            pressed_key_code = CG.CGEventGetIntegerValueField(event, CG.kCGKeyboardEventKeycode)
            pressed_modifiers = CG.CGEventGetFlags(event)

            if pressed_key_code == self.key_code:
                if self.modifiers is None or (pressed_modifiers & self.modifiers) == self.modifiers:
                    logger.info(f"Клавиша {self.key_code} с модификаторами {self.modifiers} нажата.")
                    self.callback()
        return event

    def start_listener(self):
        """
        Запускает глобальный слушатель клавиш.

        :return: True, если слушатель успешно запущен.
        :raises RuntimeError: Если создание обработчика событий не удалось.
        """
        if self.event_tap:
            logger.warning("Слушатель клавиш уже запущен.")
            return False

        event_mask = (1 << CG.kCGEventKeyDown)  # Отслеживаем только нажатия клавиш
        self.event_tap = CG.CGEventTapCreate(
            CG.kCGSessionEventTap,
            CG.kCGHeadInsertEventTap,
            CG.kCGEventTapOptionDefault,
            event_mask,
            self._key_event_callback,
            None
        )

        if not self.event_tap:
            raise RuntimeError("Не удалось создать обработчик событий. Проверьте разрешения.")

        CG.CGEventTapEnable(self.event_tap, True)

        self.run_loop_source = CG.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
        CG.CFRunLoopAddSource(CG.CFRunLoopGetCurrent(), self.run_loop_source, CG.kCFRunLoopDefaultMode)

        logger.info("Слушатель клавиш успешно запущен.")
        return True

    def stop_listener(self):
        """
        Останавливает слушатель клавиш и освобождает ресурсы.
        """
        if self.event_tap:
            CG.CGEventTapEnable(self.event_tap, False)

        if self.run_loop_source:
            CG.CFRunLoopRemoveSource(CG.CFRunLoopGetCurrent(), self.run_loop_source, CG.kCFRunLoopDefaultMode)
            self.run_loop_source = None

        self.event_tap = None
        logger.info("Слушатель клавиш успешно остановлен.")