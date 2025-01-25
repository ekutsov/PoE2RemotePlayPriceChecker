import Quartz.CoreGraphics as CG

class KeyListener:
    def __init__(self, key_code, modifiers, on_key_pressed_callback):
        """
        Инициализация слушателя клавиш.

        :param key_code: Код клавиши, которая должна быть нажата (например, 14 для 'E').
        :param modifiers: Модификаторы клавиш (например, CG.kCGEventFlagMaskControl для Ctrl). Если None, модификаторы не проверяются.
        :param on_key_pressed_callback: Функция обратного вызова, которая будет вызвана при нажатии клавиши.
        """
        if not callable(on_key_pressed_callback):
            raise ValueError("on_key_pressed_callback должен быть функцией.")
        self.key_code = key_code
        self.modifiers = modifiers
        self.on_key_pressed_callback = on_key_pressed_callback
        self.event_tap = None

    def start_listener(self):
        """
        Запуск глобального слушателя клавиш.

        Слушатель отслеживает нажатие клавиш и вызывает callback-функцию при нажатии заданной комбинации.
        """
        def key_event_callback(proxy, event_type, event, refcon):
            """
            Обработчик событий нажатия клавиш.

            :param proxy: Прокси для событий.
            :param event_type: Тип события (нажатие или отпускание клавиши).
            :param event: Событие нажатия клавиши.
            :param refcon: Дополнительная информация.
            :return: Событие для дальнейшей обработки.
            """
            if event_type == CG.kCGEventKeyDown:
                pressed_key_code = CG.CGEventGetIntegerValueField(event, CG.kCGKeyboardEventKeycode)
                pressed_modifiers = CG.CGEventGetFlags(event)

                # Проверяем, совпадает ли код клавиши
                if pressed_key_code == self.key_code:
                    # Если модификаторы заданы, проверяем их
                    if self.modifiers is None or (pressed_modifiers & self.modifiers) == self.modifiers:
                        self.on_key_pressed_callback()  # Вызов callback при нажатии нужной комбинации
            return event

        # Указываем, что нас интересуют события нажатия и отпускания клавиш
        event_mask = (1 << CG.kCGEventKeyDown) | (1 << CG.kCGEventKeyUp)

        # Создаем обработчик событий
        self.event_tap = CG.CGEventTapCreate(
            CG.kCGSessionEventTap,  # Тип события: глобальные события
            CG.kCGHeadInsertEventTap,  # Вставляем событие в начало очереди
            CG.kCGEventTapOptionDefault,  # Стандартные параметры
            event_mask,  # Маска событий: нажатие и отпускание клавиш
            key_event_callback,  # Обработчик событий
            None  # Дополнительная информация (не используется)
        )

        if not self.event_tap:
            raise RuntimeError("Не удалось создать обработчик событий. Проверьте разрешения.")

        # Включаем обработчик событий
        CG.CGEventTapEnable(self.event_tap, True)

        # Добавляем обработчик событий в цикл обработки событий
        run_loop_source = CG.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
        CG.CFRunLoopAddSource(CG.CFRunLoopGetCurrent(), run_loop_source, CG.kCFRunLoopDefaultMode)

        return True

    def update_key_combination(self, key_code, modifiers=None):
        """
        Обновление комбинации клавиш для отслеживания.

        :param key_code: Новый код клавиши.
        :param modifiers: Новые модификаторы клавиш. Если None, модификаторы не проверяются.
        """
        self.key_code = key_code
        self.modifiers = modifiers
        print(f"Комбинация клавиш обновлена: {key_code}, модификаторы: {modifiers}")