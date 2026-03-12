from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
from scanner.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self, bundle_identifier, app_name, app_icon):
        super(MainWindow, self).__init__()
        self._settings = Settings(bundle_identifier, app_name)
        self._app_icon = app_icon
        self.init()

    def init(self):
        self.setWindowTitle('My Scanner')
        print(f'Settings path: {self.settings().fileName()}')
        self.setWindowIcon(self.app_icon())
        # self.load_geometry_and_state()
        # self.init_default_menus()
        self.statusBar().showMessage('Ready')

    def settings(self):
        return self._settings

    def app_icon(self):
        return self._app_icon