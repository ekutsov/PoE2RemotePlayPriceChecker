import Quartz.CoreGraphics as CG
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import tensorflow as tf
from logger_config import logger


class ScreenshotHandler:
    """
    Класс для захвата скриншота, увеличения изображения в 4 раза с помощью TensorFlow,
    и дополнительной предобработки для улучшения распознавания текста.
    """

    @staticmethod
    def take_screenshot(rect):
        """
        Делает скриншот заданной области (глобальные координаты), возвращая
        уже предобработанное PIL.Image (Grayscale, binarized) для лучшего OCR.

        Шаги:
         1) Захват скриншота (RGBA).
         2) Увеличение в 4 раза (bicubic, TensorFlow).
         3) Предобработка (grayscale, contrast, noise filter, threshold).

        :param rect: ((x, y), (width, height)) - координаты области в CoreGraphics.
        :return: PIL.Image (монохромное, бинаризованное), или None при ошибке.
        """
        try:
            (x, y), (width, height) = rect
            capture_rect = CG.CGRectMake(x, y, width, height)

            image_ref = CG.CGWindowListCreateImage(
                capture_rect,
                CG.kCGWindowListOptionOnScreenBelowWindow,
                CG.kCGNullWindowID,
                CG.kCGWindowImageDefault
            )
            if not image_ref:
                logger.error("Не удалось создать CGImage (image_ref == None).")
                return None

            w = CG.CGImageGetWidth(image_ref)
            h = CG.CGImageGetHeight(image_ref)
            bytes_per_row = CG.CGImageGetBytesPerRow(image_ref)
            data_provider = CG.CGImageGetDataProvider(image_ref)
            raw_data = CG.CGDataProviderCopyData(data_provider)

            data = np.frombuffer(raw_data, dtype=np.uint8)
            total_bytes = len(data)
            bytes_per_pixel = 4  # BGRA (4 байта на пиксель)

            # Проверяем, достаточно ли байт для изображения
            expected_bytes = bytes_per_row * h
            if total_bytes < expected_bytes:
                logger.error("Недостаточно байт для полного изображения.")
                return None

            # Создаем массив (h, w, 4), учитывая выравнивание
            out = np.zeros((h, w, 4), dtype=np.uint8)
            for row_index in range(h):
                start = row_index * bytes_per_row
                end = start + (w * bytes_per_pixel)
                out[row_index, :, :] = data[start:end].reshape((w, 4))

            # Меняем порядок каналов с BGRA на RGBA
            out = out[:, :, [2, 1, 0, 3]]

            pil_image = Image.fromarray(out, "RGBA")

            # 1) Увеличение изображения (4x) через TensorFlow
            upscaled = ScreenshotHandler.upscale_with_tensorflow(pil_image, scale=4)
            if upscaled is None:
                logger.error("Ошибка при апсемплинге через TensorFlow.")
                return None

            logger.info("Изображение успешно увеличено в 4 раза (bicubic).")

            # 2) Предобработка для OCR (grayscale, контраст, фильтр, бинаризация)
            processed = ScreenshotHandler.preprocess_for_ocr(upscaled)

            # # (Необязательно) сохранить для отладки
            # processed.save("screenshot_processed.png")
            # logger.info("Сохранено промежуточное изображение screenshot_processed.png")

            return processed

        except Exception as e:
            logger.error("Ошибка при получении/обработке скриншота: %s", e, exc_info=True)
            return None

    @staticmethod
    def upscale_with_tensorflow(pil_image: Image.Image, scale=4) -> Image.Image:
        """
        Увеличивает изображение (RGBA) в `scale` раз с помощью TensorFlow (bicubic resize).
        Возвращает PIL.Image или None при ошибке.
        """
        try:
            np_img = np.array(pil_image)  # (H, W, 4)
            h, w, c = np_img.shape
            if c != 4:
                logger.warning("Изображение не RGBA, найдено каналов = %d", c)

            # Преобразуем в float32 и нормализуем [0..1]
            tf_img = tf.convert_to_tensor(np_img, dtype=tf.float32) / 255.0
            # Добавляем измерение batch: [1, H, W, C]
            tf_img = tf.expand_dims(tf_img, axis=0)

            new_h = h * scale
            new_w = w * scale

            # Bicubic resize
            upscaled = tf.image.resize(
                tf_img,
                size=[new_h, new_w],
                method=tf.image.ResizeMethod.BICUBIC
            )

            # Убираем batch
            upscaled = tf.squeeze(upscaled, axis=0)

            # Переводим обратно в [0..255] uint8
            upscaled_uint8 = tf.clip_by_value(upscaled * 255.0, 0, 255)
            upscaled_uint8 = tf.cast(upscaled_uint8, tf.uint8)
            upscaled_np = upscaled_uint8.numpy()

            # Создаем PIL.Image
            result_image = Image.fromarray(upscaled_np, "RGBA")
            return result_image

        except Exception as e:
            logger.error("Ошибка при апсемплинге TensorFlow: %s", e, exc_info=True)
            return None

    @staticmethod
    def preprocess_for_ocr(pil_image: Image.Image) -> Image.Image:
        """
        Дополнительная предобработка изображения для улучшения OCR:
          - Перевод в Grayscale
          - Повышение контрастности
          - Удаление шумов (MedianFilter)
          - Бинаризация (Threshold)
        Возвращает итоговое PIL.Image (монохром + бинаризация).
        """
        # 1) Grayscale
        gray = pil_image.convert("L")

        # 2) Повышаем контрастность (коэффициент 2.0, можно регулировать)
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.0)

        # 3) Фильтр (медианный) для удаления мелких шумов
        filtered = high_contrast.filter(ImageFilter.MedianFilter(size=3))

        # 4) Бинаризация
        threshold = 128
        binarized = filtered.point(lambda p: 255 if p > threshold else 0)

        return binarized