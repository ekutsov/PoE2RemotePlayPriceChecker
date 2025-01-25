import sys
import logging

# 1) Создаём (или получаем) глобальный логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 2) Обработчик записи в файл
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# 3) Формат логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# 4) Добавляем обработчик к логгеру
logger.addHandler(file_handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Глобальная обработка необработанных исключений:
    записываем полную информацию об ошибке в лог-файл.
    """
    # Если это Ctrl+C / KeyboardInterrupt, передаём стандартному обработчику.
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Unhandled exception:", exc_info=(exc_type, exc_value, exc_traceback))