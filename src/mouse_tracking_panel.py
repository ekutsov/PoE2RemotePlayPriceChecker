import objc
import pytesseract
from AppKit import (
    NSPanel,
    NSColor,
    NSScreen,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
    NSStatusWindowLevel,
    NSWindowCollectionBehaviorFullScreenAuxiliary
)
from Quartz import (
    CGPathCreateMutable,
    CGPathAddRect,
    CGRectMake,
    CAShapeLayer
)

from logger_config import logger


class MouseTrackingPanel(NSPanel):
    """
    Панель, позволяющая «рисовать» выделенную область мышью
    (mouseDown/Dragged/Up) и, при отпускании, делать скриншот
    выбранного региона (через ScreenshotHandler).
    Поддерживает fullscreen-пространство (NSWindowCollectionBehaviorFullScreenAuxiliary).
    """

    @classmethod
    def create_panel(cls, rect, screenshot_handler=None, overlay=None):
        """
        Создаёт и инициализирует MouseTrackingPanel в указанных координатах.

        :param rect: Кортеж ((x, y), (width, height)), глобальные координаты на экране.
        :param screenshot_handler: Экземпляр ScreenshotHandler для сохранения скриншота.
        :param overlay: Ссылка на Overlay, чтобы закрыть панель вызовом overlay.finish_selection().
        :return: Экземпляр MouseTrackingPanel.
        """
        (global_x, global_y), (w, h) = rect

        panel = cls.alloc().initWithContentRect_styleMask_backing_defer_(
            ((global_x, global_y), (w, h)),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            2,  # NSBackingStoreBuffered
            False
        )

        panel.setLevel_(NSStatusWindowLevel)
        panel.setCollectionBehavior_(NSWindowCollectionBehaviorFullScreenAuxiliary)
        panel.setIgnoresMouseEvents_(False)
        panel.setAcceptsMouseMovedEvents_(True)
        panel.setAlphaValue_(0.1)

        # Включаем слой для contentView
        content_view = panel.contentView()
        content_view.setWantsLayer_(True)

        # Создаём CAShapeLayer для визуализации выделенной области
        selection_layer = CAShapeLayer.layer()
        # selection_layer.setFillColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.6, 1.0, 0.3).CGColor())
        selection_layer.setStrokeColor_(NSColor.greenColor().CGColor())
        selection_layer.setLineWidth_(2.0)
        content_view.layer().addSublayer_(selection_layer)

        # Инициализация внутренних полей
        panel._selectionLayer = selection_layer
        panel._startPoint = (0, 0)
        panel._endPoint = (0, 0)
        panel._dragging = False
        panel._windowOrigin = (global_x, global_y)
        panel._screenshot_handler = screenshot_handler
        panel._overlay = overlay

        return panel

    @staticmethod
    def canBecomeKeyWindow() -> bool:
        """Разрешаем панели становиться «ключевым» окном."""
        return True

    @staticmethod
    def canBecomeMainWindow() -> bool:
        """Разрешаем панели становиться «основным» окном."""
        return True

    def mouseDown_(self, event):
        """
        Начало выделения: запоминаем точку нажатия.
        """
        self._dragging = True
        self._startPoint = event.locationInWindow()
        self._endPoint = self._startPoint
        self.updateSelectionLayer()

        objc.super(MouseTrackingPanel, self).mouseDown_(event)

    def mouseDragged_(self, event):
        """
        Продолжение выделения: обновляем конечную точку при движении мыши.
        """
        if self._dragging:
            self._endPoint = event.locationInWindow()
            self.updateSelectionLayer()

        objc.super(MouseTrackingPanel, self).mouseDragged_(event)

    def mouseUp_(self, event):
        """
        Завершение выделения: делаем скриншот и закрываем панель.
        """
        try:
            if self._dragging:
                self._endPoint = event.locationInWindow()
                self._dragging = False
                self.updateSelectionLayer()

                rect_local = self.selectionRect()
                global_rect = self.local_rect_to_global(rect_local)

                if self._screenshot_handler:
                    pil_image = self._screenshot_handler.take_screenshot(global_rect)
                    if pil_image and self._overlay:
                        # Парсим текст через pytesseract
                        parsed_text = pytesseract.image_to_string(pil_image, "rus+eng", "--psm 6")
                        self._overlay.finish_selection(parsed_text)
                else:
                    self.close()

            objc.super(MouseTrackingPanel, self).mouseUp_(event)
        except Exception as e:
            logger.error("[mouseUp_] Exception: %s", e, exc_info=True)

    @objc.python_method
    def process_parsed_text(self, text):
        """
        Обрабатывает распознанный текст, передавая его в Overlay для отображения.
        """
        if self._overlay:
            self._overlay.show_text_editor(text)

    @objc.python_method
    def local_rect_to_global(self, local_rect):
        """
        Переводит локальные координаты (Cocoa, с нижним левым углом)
        в глобальные (CoreGraphics, с верхним левым углом).
        """
        lx, ly, w, h = local_rect
        ox, oy = self._windowOrigin
        screen_height = NSScreen.mainScreen().frame().size.height
        gy = screen_height - (oy + ly) - h
        gx = ox + lx
        return (gx, gy), (w, h)

    def updateSelectionLayer(self):
        """
        Обновляет CAShapeLayer в соответствии с текущим прямоугольником выделения.
        """
        x, y, w, h = self.selectionRect()
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(x, y, w, h))
        self._selectionLayer.setPath_(path)

    def selectionRect(self):
        """
        Возвращает текущий прямоугольник выделения в локальных координатах:
        (x, y, width, height).
        """
        sx, sy = self._startPoint
        ex, ey = self._endPoint
        x = min(sx, ex)
        y = min(sy, ey)
        w = abs(ex - sx)
        h = abs(ey - sy)
        return x, y, w, h