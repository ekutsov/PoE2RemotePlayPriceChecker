from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import numpy as np
import re

class ScreenshotHandler:
    def __init__(self, window):
        self.window = window

    def take_screenshot(self, rect):
        """Создание скриншота выделенной области и извлечение текста."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(
            self.window.winId(), rect.x(), rect.y(), rect.width(), rect.height()
        )

        # Преобразуем QPixmap в QImage
        qimage = screenshot.toImage()

        # Преобразуем QImage в массив байтов (numpy array)
        buffer = qimage.bits()
        buffer.setsize(qimage.byteCount())
        image_array = np.array(buffer).reshape(qimage.height(), qimage.width(), 4)  # 4 канала (RGBA)

        # Создаем изображение Pillow из массива
        pil_image = Image.fromarray(image_array, 'RGBA')

        # Предобработка изображения
        processed_image = self.preprocess_image(pil_image)

        # Сохраняем обработанное изображение
        processed_image.save("processed_screenshot.png", "PNG")
        print("Обработанное изображение сохранено как 'processed_screenshot.png'")

        # Используем Tesseract для извлечения текста
        extracted_text = pytesseract.image_to_string(processed_image, lang="eng+rus")

        final_text = self.clean_text(extracted_text)
        # Выводим извлеченный текст
        print("Извлеченный текст:")
        print(final_text)

    def preprocess_image(self, image):
        """Предобработка изображения для повышения качества OCR."""
        # Увеличиваем разрешение
        scale_factor = 2  # Увеличиваем размер в 2 раза
        new_size = (image.width * scale_factor, image.height * scale_factor)
        image = image.resize(new_size, Image.LANCZOS)

        # Конвертируем в оттенки серого
        image = image.convert("L")

        # Повышаем контрастность
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Увеличиваем контрастность в 2 раза

        # Применяем фильтр для удаления шумов
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Бинаризация изображения (пороговое преобразование)
        threshold = 128
        image = image.point(lambda p: p > threshold and 255)

        return image

    def clean_text(self, text):
        # Удаляем нежелательные символы, оставляя буквы, цифры, пробелы и знаки пунктуации
        cleaned_text = re.sub(r"[^а-яА-Яa-zA-Z0-9\s.,!?%\-–:;'\"]+", "", text)
        return cleaned_text