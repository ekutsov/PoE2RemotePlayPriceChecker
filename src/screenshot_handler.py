import Quartz.CoreGraphics as CG
import numpy as np
from PIL import Image


class ScreenshotHandler:
    """
    Простой класс для сохранения скриншота указанной области экрана.
    """

    @staticmethod
    def save_screenshot(rect):
        """
        Сохраняет скриншот заданного прямоугольника (глобальные координаты) в PNG-файл.

        :param rect: ((x, y), (width, height)) - координаты и размер области.
        :return: True, если успешно; False в случае ошибки.
        """

        try:
            # 1. Разбираем координаты
            (x, y), (width, height) = rect

            # 2. Создаём CGRect
            capture_rect = CG.CGRectMake(x, y, width, height)

            # 3. Захватываем изображение
            image_ref = CG.CGWindowListCreateImage(
                capture_rect,
                CG.kCGWindowListOptionOnScreenBelowWindow,
                CG.kCGNullWindowID,
                CG.kCGWindowImageDefault
            )
            if not image_ref:
                print("Не удалось создать CGImage (image_ref == None).")
                return False

            # 4. Параметры изображения
            w = CG.CGImageGetWidth(image_ref)
            h = CG.CGImageGetHeight(image_ref)
            bytes_per_row = CG.CGImageGetBytesPerRow(image_ref)  # с учётом выравнивания
            data_provider = CG.CGImageGetDataProvider(image_ref)
            raw_data = CG.CGDataProviderCopyData(data_provider)

            # 5. Читаем байты в numpy-массив
            data = np.frombuffer(raw_data, dtype=np.uint8)
            total_bytes = len(data)

            bytes_per_pixel = 4  # RGBA (4 байта на пиксель)

            # Готовим массив нужного размера (h, w, 4)
            out = np.zeros((h, w, 4), dtype=np.uint8)

            # 6. Копируем строки построчно (с учётом выравнивания)
            row_start = 0
            for row_index in range(h):
                row_end = row_start + (w * bytes_per_pixel)
                if row_end > total_bytes:
                    print(f"Ошибка: не хватает данных для строки {row_index}.")
                    return False

                out[row_index, :, :] = data[row_start:row_end].reshape((1, w, 4))
                row_start += bytes_per_row

            # 7. Создаём PIL-изображение и сохраняем
            pil_image = Image.fromarray(out, "RGBA")
            pil_image.save("screenshot.png")

            print(f"Скриншот успешно сохранён в 'screenshot.png'")
            return True

        except Exception as e:
            print("Ошибка при сохранении скриншота:", e)
            return False
