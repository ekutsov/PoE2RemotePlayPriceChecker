import objc
import json
from AppKit import (
    NSPanel, NSColor, NSScreen, NSTextView, NSScrollView, NSButton,
    NSMakeRect, NSPoint, NSSize, NSView, NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel, NSStatusWindowLevel,
    NSWindowCollectionBehaviorFullScreenAuxiliary, NSTextField, NSFont,
    NSShadow, NSImage, NSBezierPath, NSLineBreakByWordWrapping,
    NSViewWidthSizable, NSViewHeightSizable, NSViewMinXMargin, NSViewMinYMargin, NSViewMaxYMargin,
    NSRoundedBezelStyle, NSRoundRectBezelStyle, NSCenterTextAlignment,
    NSBezelStyleCircular, NSURL, NSImageView, NSImageScaleAxesIndependently
)
from Quartz import CGRectMake
from typing import Optional, Tuple, Callable

# Константы для размеров и отступов
PANEL_WIDTH = 400
PANEL_HEIGHT = 400
MARGIN = 10
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
    def create_panel(cls, json_text: str, on_save_callback: Optional[Callable] = None, on_close_callback: Optional[Callable] = None) -> 'TextEditorOverlay':
        """
        Создаёт панель TextEditorOverlay с хедером предмета.
        Принимает JSON строку с данными предмета.
        """
        try:
            item_data = json.loads(json_text)
            item_name = item_data.get("name", "Unknown Item")
            unique_base = item_data.get("unique", {}).get("base", "Unknown Base")
        except json.JSONDecodeError:
            item_name = "Invalid JSON"
            unique_base = "Unknown Base"

        screen = NSScreen.mainScreen()
        screen_frame = screen.frame() if screen else CGRectMake(0, 0, PANEL_WIDTH, PANEL_HEIGHT)

        panel_x = (screen_frame.size.width - PANEL_WIDTH) / 2
        panel_y = (screen_frame.size.height - PANEL_HEIGHT) / 2
        rect = CGRectMake(panel_x, panel_y, PANEL_WIDTH, PANEL_HEIGHT)

        panel = cls.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            2,  # NSBackingStoreBuffered
            False
        )

        panel._setup_panel()
        panel._initialize_ui(item_name, unique_base, json_text, on_save_callback, on_close_callback)

        return panel

    def _setup_panel(self):
        """Настройка панели."""
        self.setLevel_(NSStatusWindowLevel)
        self.setCollectionBehavior_(NSWindowCollectionBehaviorFullScreenAuxiliary)
        self.setBackgroundColor_(NSColor.clearColor())
        self.setAlphaValue_(1.0)
        self.setIgnoresMouseEvents_(False)
        self.setAcceptsMouseMovedEvents_(True)

        content_view = self.contentView()
        content_view.setWantsLayer_(True)

        background_view = NSView.alloc().initWithFrame_(content_view.bounds())
        background_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        background_view.setWantsLayer_(True)
        background_view.layer().setBackgroundColor_(NSColor.windowBackgroundColor().CGColor())
        background_view.layer().setCornerRadius_(CORNER_RADIUS)
        background_view.layer().setMasksToBounds_(True)

        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.5))
        shadow.setShadowBlurRadius_(20)
        shadow.setShadowOffset_((0, -5))
        background_view.setShadow_(shadow)

        content_view.addSubview_(background_view)

    def _initialize_ui(self, item_name: str, unique_base: str, text: str, on_save_callback: Optional[Callable], on_close_callback: Optional[Callable]):
        """Инициализация элементов интерфейса."""
        content_view = self.contentView()

        header_view = self._add_header(content_view, item_name, unique_base)
        content_view.addSubview_(header_view)

        text_view = self._add_text_view(content_view, text, header_view.frame().size.height)
        self._text_view = text_view

        self._add_buttons(content_view)

        self._on_save_callback = on_save_callback
        self._on_close_callback = on_close_callback

        self._is_dragging = False
        self._drag_start_point = NSPoint(0, 0)

        self.makeKeyAndOrderFront_(None)
        self.makeFirstResponder_(text_view)

    @staticmethod
    def _add_header(content_view: NSView, item_name: str, unique_base: str) -> NSView:
        """Добавляет хедер предмета с фоновыми изображениями и текстом."""
        header_height = 50
        header_view = NSView.alloc().initWithFrame_(
            NSMakeRect(0, content_view.frame().size.height - header_height, content_view.frame().size.width, header_height))
        header_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)

        left_image_url = NSURL.URLWithString_("https://web.poecdn.com/protected/image/item/popup2/header-double-unique-left.png?v=1732003056293&key=qrl8M2m852PSVfYgs7nT9g")
        middle_image_url = NSURL.URLWithString_("https://web.poecdn.com/protected/image/item/popup2/header-double-unique-middle.png?v=1732003056293&key=wxQkVW4aTky07SUpkACvSA")
        right_image_url = NSURL.URLWithString_("https://web.poecdn.com/protected/image/item/popup2/header-double-unique-right.png?v=1732003056293&key=o1T64-ZQYCasntgXT_L8SA")

        left_image = NSImage.alloc().initWithContentsOfURL_(left_image_url)
        middle_image = NSImage.alloc().initWithContentsOfURL_(middle_image_url)
        right_image = NSImage.alloc().initWithContentsOfURL_(right_image_url)

        left_image_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, 46, header_height))
        left_image_view.setImage_(left_image)
        header_view.addSubview_(left_image_view)

        middle_image_view = NSImageView.alloc().initWithFrame_(NSMakeRect(46, 0, content_view.frame().size.width - 92, header_height))
        middle_image_view.setImageScaling_(NSImageScaleAxesIndependently)
        middle_image_view.setImage_(middle_image)
        header_view.addSubview_(middle_image_view)

        right_image_view = NSImageView.alloc().initWithFrame_(NSMakeRect(content_view.frame().size.width - 46, 0, 46, header_height))
        right_image_view.setImage_(right_image)
        header_view.addSubview_(right_image_view)

        text_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.686, 0.376, 0.145, 1.0)

        title_field = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 25, content_view.frame().size.width - 20, 20))
        title_field.setStringValue_(item_name)
        title_field.setFont_(NSFont.boldSystemFontOfSize_(16))
        title_field.setTextColor_(text_color)
        title_field.setBackgroundColor_(NSColor.clearColor())
        title_field.setBordered_(False)
        title_field.setEditable_(False)
        title_field.setSelectable_(False)
        title_field.setAlignment_(NSCenterTextAlignment)
        title_field.setLineBreakMode_(NSLineBreakByWordWrapping)
        header_view.addSubview_(title_field)

        base_field = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 5, content_view.frame().size.width - 20, 20))
        base_field.setStringValue_(unique_base)
        base_field.setFont_(NSFont.boldSystemFontOfSize_(16))
        base_field.setTextColor_(text_color)
        base_field.setBackgroundColor_(NSColor.clearColor())
        base_field.setBordered_(False)
        base_field.setEditable_(False)
        base_field.setSelectable_(False)
        base_field.setAlignment_(NSCenterTextAlignment)
        base_field.setLineBreakMode_(NSLineBreakByWordWrapping)
        header_view.addSubview_(base_field)

        return header_view

    @staticmethod
    def _add_text_view(content_view: NSView, text: str, header_height: float) -> NSTextView:
        """Добавляет текстовое поле для редактирования."""
        scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(MARGIN, MARGIN + BUTTON_SIZE[1] + BUTTON_MARGIN,
                       content_view.frame().size.width - 2 * MARGIN,
                       content_view.frame().size.height - header_height - BUTTON_SIZE[1] - 3 * MARGIN)
        )
        scroll_view.setBorderType_(0)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        text_view = NSTextView.alloc().initWithFrame_(scroll_view.bounds())
        text_view.setString_(text)
        text_view.setFont_(NSFont.systemFontOfSize_(FONT_SIZE_DEFAULT))
        text_view.setEditable_(True)
        text_view.setSelectable_(True)
        text_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        scroll_view.setDocumentView_(text_view)
        content_view.addSubview_(scroll_view)
        return text_view

    def _add_buttons(self, content_view: NSView):
        """Добавляет кнопки "Закрыть" и "Сохранить" на панель."""
        buttons_container = NSView.alloc().initWithFrame_(
            NSMakeRect(content_view.frame().size.width - MARGIN - BUTTON_SIZE[0] - BUTTON_SIZE[0] - BUTTON_SPACING,
                      MARGIN,
                      BUTTON_SIZE[0] + BUTTON_SIZE[0] + BUTTON_SPACING,
                      max(BUTTON_SIZE[1], BUTTON_SIZE[1]))
        )
        buttons_container.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxYMargin)
        content_view.addSubview_(buttons_container)

        close_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, (buttons_container.frame().size.height - BUTTON_SIZE[1]) / 2,
                      BUTTON_SIZE[0], BUTTON_SIZE[1])
        )
        close_button.setTitle_(CLOSE_BUTTON_TITLE)
        close_button.setBezelStyle_(NSRoundRectBezelStyle)
        close_button.setAutoresizingMask_(NSViewMinXMargin)
        close_button.setTarget_(self)
        close_button.setAction_(objc.selector(self.close_panel, signature=b'v@:@'))
        buttons_container.addSubview_(close_button)

        save_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(BUTTON_SIZE[0] + BUTTON_SPACING, (buttons_container.frame().size.height - BUTTON_SIZE[1]) / 2,
                      BUTTON_SIZE[0], BUTTON_SIZE[1])
        )
        save_button.setTitle_(SAVE_BUTTON_TITLE)
        save_button.setBezelStyle_(NSRoundRectBezelStyle)
        save_button.setAutoresizingMask_(NSViewMinXMargin)
        save_button.setTarget_(self)
        save_button.setAction_(objc.selector(self.save_text, signature=b'v@:@'))
        buttons_container.addSubview_(save_button)

    def mouseDown_(self, event):
        """Начало перетаскивания окна."""
        self._is_dragging = True
        self._drag_start_point = event.locationInWindow()

    def mouseDragged_(self, event):
        """Перетаскивание окна."""
        if self._is_dragging:
            current_point = event.locationInWindow()
            dx = current_point.x - self._drag_start_point.x
            dy = current_point.y - self._drag_start_point.y

            frame = self.frame()
            new_origin = NSPoint(frame.origin.x + dx, frame.origin.y + dy)
            self.setFrameOrigin_(new_origin)

    def mouseUp_(self, event):
        """Завершение перетаскивания окна."""
        self._is_dragging = False

    @objc.IBAction
    def save_text(self, sender):
        """Сохраняет текст из текстового поля и вызывает callback."""
        edited_text = self._text_view.string()
        if self._on_save_callback:
            self._on_save_callback(edited_text)

    @objc.IBAction
    def close_panel(self, sender):
        """Закрывает панель."""
        if self._on_close_callback:
            self._on_close_callback()

    def canBecomeKeyWindow(self) -> bool:
        """Разрешаем панели становиться ключевым окном."""
        return True

    def canBecomeMainWindow(self) -> bool:
        """Разрешаем панели становиться основным окном."""
        return True