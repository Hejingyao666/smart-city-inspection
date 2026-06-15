import sys
import os

os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt

from odp_desktop.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ODPlatform")
    app.setApplicationVersion("0.1.0")
    
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()