import objc
from AppKit import (
    NSPanel, NSColor, NSScreen, NSTextView, NSScrollView, NSButton,
    NSMakeRect, NSPoint, NSSize, NSView, NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel, NSStatusWindowLevel,
    NSWindowCollectionBehaviorFullScreenAuxiliary, NSTextField, NSFont,
    NSShadow, NSImage, NSBezierPath,
    NSViewWidthSizable, NSViewHeightSizable, NSViewMinXMargin, NSViewMaxYMargin,
    NSRoundedBezelStyle, NSRoundRectBezelStyle,
    NSBezelStyleCircular
)
from Quartz import CGRectMake

# Константы для размеров и отступов
PANEL_WIDTH = 800
PANEL_HEIGHT = 600
MARGIN = 10
BUTTON_SIZE = 12  # Уменьшено до стандартного размера
BUTTON_MARGIN = 10
BUTTON_SIZE = (100, 30)
BUTTON_SPACING = 10  # Расстояние между кнопками
TITLE_TEXT = "Редактирование текста"
SAVE_BUTTON_TITLE = "Сохранить"
CLOSE_BUTTON_TITLE = "Закрыть"
FONT_SIZE_TITLE = 14
FONT_SIZE_DEFAULT = 12
CORNER_RADIUS = 12

class TextEditorOverlay(NSPanel):
    """
    Панель для редактирования текста с улучшенным UI,
    поддержкой перетаскивания и кнопками управления, имитирующая стиль macOS.
    """

    @classmethod
    def create_panel(cls, text: str, on_save_callback=None, on_close_callback=None) -> 'TextEditorOverlay':
        """
        Создаёт панель TextEditorOverlay.

        :param text: Текст для редактирования.
        :param on_save_callback: Callback для сохранения изменений.
        :param on_close_callback: Callback для закрытия окна
        :return: Экземпляр TextEditorOverlay.
        """
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame() if screen else CGRectMake(0, 0, PANEL_WIDTH, PANEL_HEIGHT)

        panel_x = (screen_frame.size.width - PANEL_WIDTH) / 2
        panel_y = (screen_frame.size.height - PANEL_HEIGHT) / 2
        rect = CGRectMake(panel_x, panel_y, PANEL_WIDTH, PANEL_HEIGHT)

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
        panel.setBackgroundColor_(NSColor.clearColor())  # Используем прозрачный фон для тени
        panel.setAlphaValue_(1.0)
        panel.setIgnoresMouseEvents_(False)
        panel.setAcceptsMouseMovedEvents_(True)

        # Контейнер для UI с закругленными углами и фоном
        content_view = panel.contentView()

        # Устанавливаем слой для content_view
        content_view.setWantsLayer_(True)

        # Добавляем слой для фонового представления
        background_view = NSView.alloc().initWithFrame_(content_view.bounds())
        background_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        background_view.setWantsLayer_(True)
        background_view.layer().setBackgroundColor_(NSColor.windowBackgroundColor().CGColor())
        background_view.layer().setCornerRadius_(CORNER_RADIUS)
        background_view.layer().setMasksToBounds_(True)  # Ограничиваем дочерние представления границами слоя

        # Добавляем тень к background_view
        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.5))  # Черный цвет с 50% прозрачностью
        shadow.setShadowBlurRadius_(20)
        shadow.setShadowOffset_((0, -5))
        background_view.setShadow_(shadow)

        content_view.addSubview_(background_view)

        # Убираем добавление пользовательского заголовка
        # cls._add_title_bar(content_view)

        # Добавляем элементы интерфейса поверх background_view
        text_view = cls._add_text_view(content_view, text)
        cls._add_buttons(content_view, panel)

        # Привязываем callback для сохранения
        panel._text_view = text_view
        panel._on_save_callback = on_save_callback
        panel._on_close_callback = on_close_callback

        # Переменные для перетаскивания
        panel._is_dragging = False
        panel._drag_start_point = NSPoint(0, 0)

        panel.makeKeyAndOrderFront_(None)  # Отображаем панель

        # Устанавливаем фокус на текстовом поле
        panel.makeFirstResponder_(text_view)

        return panel

    @staticmethod
    def _add_text_view(content_view: NSView, text: str) -> NSTextView:
        """
        Добавляет текстовое поле для редактирования.
        """
        scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(MARGIN, MARGIN + BUTTON_SIZE[1] + BUTTON_MARGIN,
                      content_view.frame().size.width - 2 * MARGIN,
                      content_view.frame().size.height - BUTTON_SIZE[1] - 3 * MARGIN)
        )
        scroll_view.setBorderType_(0)  # Без рамки
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        text_view = NSTextView.alloc().initWithFrame_(scroll_view.bounds())
        text_view.setString_(text)
        text_view.setFont_(NSFont.systemFontOfSize_(FONT_SIZE_DEFAULT))
        text_view.setEditable_(True)      # Делает текстовое поле редактируемым
        text_view.setSelectable_(True)    # Разрешает выделение текста
        text_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        scroll_view.setDocumentView_(text_view)
        content_view.addSubview_(scroll_view)
        return text_view

    @classmethod
    def _add_buttons(cls, content_view: NSView, panel: 'TextEditorOverlay'):
        """
        Добавляет кнопки "Закрыть" и "Сохранить" на панель.
        """
        # Контейнер для кнопок
        buttons_container = NSView.alloc().initWithFrame_(
            NSMakeRect(content_view.frame().size.width - MARGIN - BUTTON_SIZE[0] - BUTTON_SIZE[0] - BUTTON_SPACING,
                      MARGIN,
                      BUTTON_SIZE[0] + BUTTON_SIZE[0] + BUTTON_SPACING,
                      max(BUTTON_SIZE[1], BUTTON_SIZE[1]))
        )
        buttons_container.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxYMargin)
        content_view.addSubview_(buttons_container)

        # Кнопка закрытия
        close_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, (buttons_container.frame().size.height - BUTTON_SIZE[1]) / 2,
                      BUTTON_SIZE[0], BUTTON_SIZE[1])
        )
        close_button.setTitle_(CLOSE_BUTTON_TITLE)
        close_button.setBezelStyle_(NSRoundRectBezelStyle)
        close_button.setAutoresizingMask_(NSViewMinXMargin)
        close_button.setTarget_(panel)
        close_button.setAction_(objc.selector(panel.close_panel, signature=b'v@:@'))
        buttons_container.addSubview_(close_button)

        # Кнопка сохранения
        save_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(BUTTON_SIZE[0] + BUTTON_SPACING, (buttons_container.frame().size.height - BUTTON_SIZE[1]) / 2,
                      BUTTON_SIZE[0], BUTTON_SIZE[1])
        )
        save_button.setTitle_(SAVE_BUTTON_TITLE)
        save_button.setBezelStyle_(NSRoundRectBezelStyle)
        save_button.setAutoresizingMask_(NSViewMinXMargin)
        save_button.setTarget_(panel)
        save_button.setAction_(objc.selector(panel.save_text, signature=b'v@:@'))
        buttons_container.addSubview_(save_button)

    def mouseDown_(self, event):
        """
        Начало перетаскивания окна.
        """
        # Позволяем перетаскивать окно по всей области панели
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

    @objc.IBAction
    def save_text(self, sender):
        """
        Сохраняет текст из текстового поля и вызывает callback.
        """
        edited_text = self._text_view.string()
        if self._on_save_callback:
            self._on_save_callback(edited_text)

    @objc.IBAction
    def close_panel(self, sender):
        """
        Закрывает панель.
        """
        if self._on_close_callback:
            self._on_close_callback()

    def canBecomeKeyWindow(self) -> bool:
        """Разрешаем панели становиться ключевым окном."""
        return True

    def canBecomeMainWindow(self) -> bool:
        """Разрешаем панели становиться основным окном."""
        return True