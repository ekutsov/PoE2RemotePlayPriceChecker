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
from typing import Optional, Tuple

from logger_config import logger


class MouseTrackingPanel(NSPanel):
    """
    Панель, позволяющая «рисовать» выделенную область мышью
    (mouseDown/Dragged/Up) и, при отпускании, делать скриншот
    выбранного региона (через ScreenshotHandler).
    Поддерживает fullscreen-пространство (NSWindowCollectionBehaviorFullScreenAuxiliary).
    """

    @classmethod
    def create_panel(cls, rect: Tuple[Tuple[float, float], Tuple[float, float]], screenshot_handler=None, finish_callback=None) -> 'MouseTrackingPanel':
        """
        Создаёт и инициализирует MouseTrackingPanel в указанных координатах.

        :param rect: Кортеж ((x, y), (width, height)), глобальные координаты на экране.
        :param screenshot_handler: Экземпляр ScreenshotHandler для сохранения скриншота.
        :param finish_callback: Callback overlay.finish_selection().
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

        panel._initialize_content_view()
        panel._initialize_selection_layer()
        panel._initialize_fields(screenshot_handler, (global_x, global_y), finish_callback)

        return panel

    def _initialize_content_view(self):
        """Инициализирует contentView и включает слой для него."""
        content_view = self.contentView()
        content_view.setWantsLayer_(True)

    def _initialize_selection_layer(self):
        """Инициализирует CAShapeLayer для визуализации выделенной области."""
        selection_layer = CAShapeLayer.layer()
        selection_layer.setStrokeColor_(NSColor.greenColor().CGColor())
        selection_layer.setLineWidth_(2.0)
        self.contentView().layer().addSublayer_(selection_layer)
        self._selectionLayer = selection_layer

    def _initialize_fields(self, screenshot_handler, window_origin, finish_callback):
        """Инициализирует внутренние поля панели."""
        self._startPoint = (0, 0)
        self._endPoint = (0, 0)
        self._dragging = False
        self._windowOrigin = window_origin
        self._screenshot_handler = screenshot_handler
        self._finish_callback = finish_callback

    @staticmethod
    def canBecomeKeyWindow() -> bool:
        """Разрешаем панели становиться «ключевым» окном."""
        return True

    @staticmethod
    def canBecomeMainWindow() -> bool:
        """Разрешаем панели становиться «основным» окном."""
        return True

    def mouseDown_(self, event):
        """Начало выделения: запоминаем точку нажатия."""
        self._dragging = True
        self._startPoint = event.locationInWindow()
        self._endPoint = self._startPoint
        self.updateSelectionLayer()

    def mouseDragged_(self, event):
        """Продолжение выделения: обновляем конечную точку при движении мыши."""
        if self._dragging:
            self._endPoint = event.locationInWindow()
            self.updateSelectionLayer()

    def mouseUp_(self, event):
        """Завершение выделения: делаем скриншот и закрываем панель."""
        try:
            if self._dragging:
                self._endPoint = event.locationInWindow()
                self._dragging = False
                self.updateSelectionLayer()

                rect_local = self.selectionRect()
                global_rect = self.local_rect_to_global(rect_local)

                if self._screenshot_handler:
                    pil_image = self._screenshot_handler.take_screenshot(global_rect)
                    if pil_image:
                        parsed_text = pytesseract.image_to_string(pil_image, "rus+eng", "--psm 6")
                        self._finish_callback(parsed_text)
                else:
                    self.close()
        except Exception as e:
            logger.error("[mouseUp_] Exception: %s", e, exc_info=True)

    @objc.python_method
    def local_rect_to_global(self, local_rect: Tuple[float, float, float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Переводит локальные координаты (Cocoa, с нижним левым углом)
        в глобальные (CoreGraphics, с верхним левым углом).

        :param local_rect: Кортеж (x, y, width, height) в локальных координатах.
        :return: Кортеж ((x, y), (width, height)) в глобальных координатах.
        """
        lx, ly, w, h = local_rect
        ox, oy = self._windowOrigin
        screen_height = NSScreen.mainScreen().frame().size.height
        gy = screen_height - (oy + ly) - h
        gx = ox + lx
        return (gx, gy), (w, h)

    def updateSelectionLayer(self):
        """Обновляет CAShapeLayer в соответствии с текущим прямоугольником выделения."""
        x, y, w, h = self.selectionRect()
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(x, y, w, h))
        self._selectionLayer.setPath_(path)

    def selectionRect(self) -> Tuple[float, float, float, float]:
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