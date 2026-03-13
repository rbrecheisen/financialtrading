import sys
from PySide6.QtWidgets import QApplication, QStyle
from scanner.mainwindow import MainWindow


def main():
    app_name = 'scanner'
    QApplication.setApplicationName(app_name)
    app = QApplication(sys.argv)
    app.setApplicationName(app_name)
    window = MainWindow(
        'nl.rbeesoft', app_name,
        app.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()