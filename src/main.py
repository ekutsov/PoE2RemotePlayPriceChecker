import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay

from logger_config import logger, handle_exception

def main():
    # Устанавливаем глобальный хук исключений
    sys.excepthook = handle_exception

    # Создаём PyQt-приложение
    app = QApplication(sys.argv)

    # Запускаем наше окно Overlay
    window = Overlay()

    logger.info("Приложение запущено.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()