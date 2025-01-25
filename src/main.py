import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay

# Подключаем наш конфиг логгера
from logger_config import logger, handle_exception

def main():
    # Устанавливаем глобальный хук исключений
    sys.excepthook = handle_exception

    # Создаём PyQt-приложение
    app = QApplication(sys.argv)

    # Запускаем наше окно Overlay
    window = Overlay()

    # Можно сразу что-то залогировать (пример)
    logger.info("Приложение запущено.")

    # Старт цикла событий
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()