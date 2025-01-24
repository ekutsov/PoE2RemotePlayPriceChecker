from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QImage
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import numpy as np
import re


class ScreenshotHandler:
    def __init__(self, window):
        self.window = window

    def take_screenshot(self, rect):
        """Создание скриншота выделенной области и возвращение обработанного изображения."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(
            self.window.winId(), rect.x(), rect.y(), rect.width(), rect.height()
        )

        qimage = screenshot.toImage()
        buffer = qimage.bits()
        buffer.setsize(qimage.byteCount())
        image_array = np.array(buffer).reshape(qimage.height(), qimage.width(), 4)  # RGBA

        pil_image = Image.fromarray(image_array, 'RGBA')
        processed_image = self.preprocess_image(pil_image)

        # Сохраняем изображение для отладки
        processed_image.save("processed_screenshot.png", "PNG")
        print("Обработанное изображение сохранено как 'processed_screenshot.png'")

        return processed_image

    def preprocess_image(self, image):
        """Предобработка изображения для повышения качества OCR."""
        # Увеличиваем разрешение
        scale_factor = max(2, 1000 // min(image.width, image.height))  # Динамическое масштабирование
        new_size = (image.width * scale_factor, image.height * scale_factor)
        image = image.resize(new_size, Image.LANCZOS)

        # Конвертируем в оттенки серого
        image = image.convert("L")

        # Повышаем контрастность
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Применяем фильтры для удаления шумов
        image = image.filter(ImageFilter.MedianFilter(size=3))
        image = image.filter(ImageFilter.EDGE_ENHANCE)

        # Бинаризация изображения
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)

        return image