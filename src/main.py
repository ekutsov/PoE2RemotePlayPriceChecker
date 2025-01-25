import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay

def main():
    app = QApplication(sys.argv)
    window = Overlay()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()