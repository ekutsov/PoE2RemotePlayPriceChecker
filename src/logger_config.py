import sys
import logging
from typing import Optional

# 1) Создаём (или получаем) глобальный логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 2) Формат логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# 3) Обработчик записи в файл
#    ВАЖНО: mode="w" перезаписывает файл при каждом новом запуске приложения
file_handler = logging.FileHandler("app.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 4) Обработчик вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """
    Глобальная обработка необработанных исключений:
    записываем полную информацию об ошибке в лог-файл и консоль.
    """
    # Если это Ctrl+C / KeyboardInterrupt, передаём стандартному обработчику.
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Unhandled exception:", exc_info=(exc_type, exc_value, exc_traceback))