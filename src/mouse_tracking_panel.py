import objc
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
    Класс-панель для отслеживания событий мыши, рисования прямоугольника выделения
    и вызова ScreenshotHandler.
    """

    def __init__(self):
        """
        Обратите внимание, что при использовании `@classmethod create_panel`
        и `alloc().init...` обычно инициализируются поля там.
        Если вы переопределяете __init__, нужно звать super().__init__().
        Но чаще всю инициализацию делают в create_panel.
        """
        # super().__init__()
        self._endPoint = None
        self._startPoint = None
        self._dragging = None

    @classmethod
    def create_panel(cls, rect, screenshot_handler=None, overlay=None):
        """
        Создаёт и возвращает готовую к использованию панель MouseTrackingPanel.

        :param rect: Кортеж ((x, y), (width, height)) - глобальные координаты окна на экране.
        :param screenshot_handler: Ссылка на ScreenshotHandler (чтобы вызвать save_screenshot).
        :param overlay: Ссылка на Overlay, чтобы при завершении скриншота вызвать finish_selection().
        """
        (global_x, global_y), (w, h) = rect

        panel = cls.alloc().initWithContentRect_styleMask_backing_defer_(
            ((global_x, global_y), (w, h)),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            2,  # backing store (NSBackingStoreBuffered)
            False
        )

        panel.setLevel_(NSStatusWindowLevel)
        panel.setCollectionBehavior_(NSWindowCollectionBehaviorFullScreenAuxiliary)

        # Разрешаем приём событий мыши
        panel.setIgnoresMouseEvents_(False)
        panel.setAcceptsMouseMovedEvents_(True)

        # Настраиваем внешний вид (полупрозрачная панель)
        # panel.setBackgroundColor_(
        #     NSColor.colorWithRed_green_blue_alpha_(0x48 / 255.0, 0x7E / 255.0, 0xAA / 255.0, 1)
        # )
        panel.setAlphaValue_(0.1)

        # -- Включаем слой для contentView (для рисования рамки выделения) --
        content_view = panel.contentView()
        content_view.setWantsLayer_(True)

        selection_layer = CAShapeLayer.layer()
        # Полупрозрачная заливка
        selection_layer.setFillColor_(
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.6, 1.0, 0.3).CGColor()
        )
        # Белая обводка
        selection_layer.setStrokeColor_(NSColor.greenColor().CGColor())
        selection_layer.setLineWidth_(2.0)
        content_view.layer().addSublayer_(selection_layer)

        # -- Сохраняем нужные данные в атрибутах --
        panel._selectionLayer = selection_layer
        panel._startPoint = (0, 0)
        panel._endPoint = (0, 0)
        panel._dragging = False

        # Координаты окна в глобальных координатах (для перевода выделения)
        panel._windowOrigin = (global_x, global_y)

        # Ссылка на ScreenshotHandler
        panel._screenshot_handler = screenshot_handler

        # Ссылка на Overlay
        panel._overlay = overlay

        return panel

    @staticmethod
    def canBecomeKeyWindow() -> bool:
        return True

    @staticmethod
    def canBecomeMainWindow() -> bool:
        return True

    def mouseDown_(self, event):
        """Начало выделения."""
        self._dragging = True
        self._startPoint = event.locationInWindow()
        self._endPoint = self._startPoint
        self.updateSelectionLayer()

        objc.super(MouseTrackingPanel, self).mouseDown_(event)

    def mouseDragged_(self, event):
        """Обновление выделения при перетаскивании."""
        if self._dragging:
            self._endPoint = event.locationInWindow()
            self.updateSelectionLayer()

        objc.super(MouseTrackingPanel, self).mouseDragged_(event)

    def mouseUp_(self, event):
        """Завершение выделения: делаем скриншот и закрываем панель."""
        try:
            if self._dragging:
                self._endPoint = event.locationInWindow()
                self._dragging = False
                self.updateSelectionLayer()

                rect_local = self.selectionRect()

                # Переводим координаты из "локальных" (в окне) в "глобальные" (экран)
                global_rect = self.local_rect_to_global(rect_local)

                # Если есть ScreenshotHandler – делаем скриншот
                if self._screenshot_handler:
                    self._screenshot_handler.save_screenshot(global_rect)

                # --- Главное: закрыть панель и вернуть всё в исходное состояние ---
                if self._overlay:
                    # У Overlay уже есть метод finish_selection(),
                    # который сделает self.panel.close() и self.panel=None.
                    self._overlay.finish_selection()
                else:
                    # Если по какой-то причине overlay не передан,
                    # просто закрываем окно:
                    self.close()

            objc.super(MouseTrackingPanel, self).mouseUp_(event)
        except Exception as e:
            logger.error("[mouseUp_] Exception:", e)

    @objc.python_method
    def local_rect_to_global(self, local_rect):
        lx, ly, w, h = local_rect
        ox, oy = self._windowOrigin  # глобальное положение окна (но тоже может быть «снизу»)

        # Определяем высоту главного экрана
        screen_height = NSScreen.mainScreen().frame().size.height

        # Если ваше окно "родилось" с origin (ox, oy) в "Cocoa-координатах" (снизу),
        # а скриншот CoreGraphics — сверху, нужно пересчитать Y.
        #
        # Допустим, окно на экране находится так: windowOrigin.y от нижнего края.
        # Но CoreGraphics ждет координаты от верхнего края экрана.
        # Тогда реальный глобальный y = (высота экрана) - (нижняя координата) - (высота лок.прямоугольника).
        #
        # Однако exact формула зависит от того, как ваш process_handler.get_screen_resolution() выдает (x, y).
        # Если (0,0) от верхнего экрана — нужно проверить.
        #
        # Наиболее частый случай, если (ox, oy) = нижний левый угол окна (Cocoa):
        gy = screen_height - (oy + ly) - h
        gx = ox + lx

        return (gx, gy), (w, h)

    def updateSelectionLayer(self):
        """Обновляет CAShapeLayer на основе selectionRect()."""
        (x, y, w, h) = self.selectionRect()
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(x, y, w, h))
        self._selectionLayer.setPath_(path)

    def selectionRect(self):
        """
        Возвращает (x, y, w, h) в локальных координатах окна
        (0,0 = левый-нижний угол, как в Cocoa).
        """
        sx, sy = self._startPoint
        ex, ey = self._endPoint
        x = min(sx, ex)
        y = min(sy, ey)
        w = abs(ex - sx)
        h = abs(ey - sy)
        return x, y, w, h