import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay
from logger_config import (
    handle_exception,
    logger
)

def main():
    sys.excepthook = handle_exception
    logger.debug("Application started")
    app = QApplication(sys.argv)
    window = Overlay()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()