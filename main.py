import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay

def main():
    target_process_name = "RemotePlay"
    app = QApplication(sys.argv)
    window = Overlay(target_process_name)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()