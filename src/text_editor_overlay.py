import objc
from AppKit import (
    NSPanel,
    NSColor,
    NSScreen,
    NSTextView,
    NSScrollView,
    NSButton,
    NSMakeRect,
    NSPoint,
    NSSize,
    NSView,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
    NSStatusWindowLevel,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSTextField,
    NSFont
)
from Quartz import CGRectMake


class TextEditorOverlay(NSPanel):
    """
    Панель для редактирования текста с улучшенным UI,
    поддержкой перетаскивания и кнопками управления.
    """

    @classmethod
    def create_panel(cls, text, on_save_callback=None):
        """
        Создаёт панель TextEditorOverlay.

        :param text: Текст для редактирования.
        :param on_save_callback: Callback для сохранения изменений.
        :return: Экземпляр TextEditorOverlay.
        """
        # Размер и положение панели (центр экрана, 800x600)
        screen_frame = NSScreen.mainScreen().frame()
        panel_width = 800
        panel_height = 600
        panel_x = (screen_frame.size.width - panel_width) / 2
        panel_y = (screen_frame.size.height - panel_height) / 2
        rect = CGRectMake(panel_x, panel_y, panel_width, panel_height)

        # Создаём панель
        panel = cls.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            2,  # NSBackingStoreBuffered
            False
        )

        # Настройка панели
        panel.setLevel_(NSStatusWindowLevel)
        panel.setCollectionBehavior_(NSWindowCollectionBehaviorFullScreenAuxiliary)
        panel.setBackgroundColor_(NSColor.whiteColor())
        panel.setAlphaValue_(1.0)
        panel.setIgnoresMouseEvents_(False)
        panel.setAcceptsMouseMovedEvents_(True)

        # Контейнер для UI
        content_view = panel.contentView()

        # Заголовок
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, panel_height - 40, panel_width - 60, 30))
        title_label.setStringValue_("Редактирование текста")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        title_label.setBezeled_(False)
        title_label.setEditable_(False)
        title_label.setDrawsBackground_(False)
        content_view.addSubview_(title_label)

        # Добавляем NSTextView для редактирования текста
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 60, panel_width - 20, panel_height - 120))
        scroll_view.setBorderType_(0)  # Без рамки
        scroll_view.setHasVerticalScroller_(True)

        text_view = NSTextView.alloc().initWithFrame_(scroll_view.frame())
        text_view.setString_(text)
        scroll_view.setDocumentView_(text_view)
        content_view.addSubview_(scroll_view)

        # Кнопка сохранения
        save_button = NSButton.alloc().initWithFrame_(NSMakeRect(panel_width - 120, 10, 100, 40))
        save_button.setTitle_("Сохранить")
        save_button.setBezelStyle_(1)
        save_button.setTarget_(panel)
        save_button.setAction_(objc.selector(cls.save_text, signature=b'v@:@'))
        content_view.addSubview_(save_button)

        # Кнопка закрытия
        close_button = NSButton.alloc().initWithFrame_(NSMakeRect(panel_width - 50, panel_height - 40, 40, 30))
        close_button.setTitle_("✕")
        close_button.setBezelStyle_(1)
        close_button.setTarget_(panel)
        close_button.setAction_(objc.selector(cls.close_panel, signature=b'v@:@'))
        content_view.addSubview_(close_button)

        # Привязываем callback для сохранения
        panel._text_view = text_view
        panel._on_save_callback = on_save_callback

        # Переменные для перетаскивания
        panel._is_dragging = False
        panel._drag_start_point = NSPoint(0, 0)

        return panel

    def mouseDown_(self, event):
        """
        Начало перетаскивания окна.
        """
        self._is_dragging = True
        self._drag_start_point = event.locationInWindow()

    def mouseDragged_(self, event):
        """
        Перетаскивание окна.
        """
        if self._is_dragging:
            current_point = event.locationInWindow()
            dx = current_point.x - self._drag_start_point.x
            dy = current_point.y - self._drag_start_point.y

            frame = self.frame()
            new_origin = NSPoint(frame.origin.x + dx, frame.origin.y + dy)
            self.setFrameOrigin_(new_origin)

    def mouseUp_(self, event):
        """
        Завершение перетаскивания окна.
        """
        self._is_dragging = False

    def save_text(self, sender):
        """
        Сохраняет текст из текстового поля и вызывает callback.
        """
        edited_text = self._text_view.string()
        if self._on_save_callback:
            self._on_save_callback(edited_text)
        self.close()

    def close_panel(self, sender):
        """
        Закрывает панель.
        """
        self.close()

    @staticmethod
    def canBecomeKeyWindow() -> bool:
        """Разрешаем панели становиться ключевым окном."""
        return True

    @staticmethod
    def canBecomeMainWindow() -> bool:
        """Разрешаем панели становиться основным окном."""
        return True