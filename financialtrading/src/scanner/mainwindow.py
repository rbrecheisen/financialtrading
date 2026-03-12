import os
import json
from pathlib import Path
from PySide6.QtCore import Qt, QByteArray, QThread
from PySide6.QtWidgets import QMainWindow, QWidget, QStyle, QLabel, QVBoxLayout, QPushButton
from PySide6.QtGui import QGuiApplication, QAction
from scanner.settings import Settings
from scanner.flaskserverworker import FlaskServerWorker

DATA_DIR = str(Path(__file__).resolve().parent)
DATA_ETFS_FILE = os.path.join(DATA_DIR, 'data/etfs.json')
DATA_STOCKS_FILE = os.path.join(DATA_DIR, 'data/stocks.json')
DATA_TOKENINFO_FILE = os.path.join(DATA_DIR, 'data/tokeninfo.json')


class MainWindow(QMainWindow):
    def __init__(self, bundle_identifier, app_name, app_icon):
        super(MainWindow, self).__init__()
        self._settings = Settings(bundle_identifier, app_name)
        self._app_icon = app_icon
        self._toggle_server_button = QPushButton('Start server')
        self._toggle_server_button.clicked.connect(self.handle_toggle_server_button)
        self._server_thread = None
        self._server_worker = None
        self._server_running = False
        self._etfs = self.load_etfs()
        self._stocks = self.load_stocks()
        self.init()

    # INITIALIZATION

    def init(self):
        self.setWindowTitle('My Scanner')
        print(f'Settings path: {self._settings.fileName()}')
        self.setWindowIcon(self._app_icon)
        self.load_geometry_and_state()
        self.init_menus()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._toggle_server_button)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def init_menus(self):
        self.init_app_menu()

    def init_app_menu(self):
        application_menu = self.menuBar().addMenu('Application')
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
        exit_action = QAction(icon, 'E&xit', self)
        exit_action.triggered.connect(self.close)
        application_menu.addAction(exit_action)

    # EVENT HANDLERS

    def closeEvent(self, event):
        self.save_geometry_and_state()
        if self._server_running and self._server_worker is not None:
            self._server_worker.stop_server()
            if self._server_thread is not None:
                self._server_thread.quit()
                self._server_thread.wait()
        return super().closeEvent(event)
    
    def handle_toggle_server_button(self):
        if self._server_running:
            self.stop_server()
        else:
            self.start_server()

    def handle_server_started(self):
        self._server_running = True
        self._toggle_server_button.setStyleSheet('background-color: green; color: white; font-weight: bold;')
        self._toggle_server_button.setText('Stop server')

    def handle_server_failed(self, e):
        print(f'Server failed ({str(e)})')
        self._server_running = False
        self._toggle_server_button.setStyleSheet('background-color: red; color: white; font-weight: bold;')
        self._toggle_server_button.setText('Start server')

    def handle_server_stopped(self):
        self._server_running = False
        self._toggle_server_button.setStyleSheet('')
        self._toggle_server_button.setText('Start server')

    # HELPERS

    def load_etfs(self):
        with open(DATA_ETFS_FILE, 'r') as f:
            data = json.load(f)
        return data

    def load_stocks(self):
        with open(DATA_STOCKS_FILE, 'r') as f:
            data = json.load(f)
        return data
    
    def load_access_token():
        with open(DATA_TOKENINFO_FILE, 'r') as f:
            data = json.load(f)
            return data['access_token']

    def start_server(self):
        self._server_thread = QThread()
        self._server_worker = FlaskServerWorker(DATA_TOKENINFO_FILE)
        self._server_worker.moveToThread(self._server_thread)
        self._server_thread.started.connect(self._server_worker.start_server)
        self._server_worker.started.connect(self.handle_server_started)
        self._server_worker.failed.connect(self.handle_server_failed)
        self._server_worker.stopped.connect(self.handle_server_stopped)
        # Clean up
        self._server_worker.stopped.connect(self._server_thread.quit)
        self._server_worker.stopped.connect(self._server_worker.deleteLater)
        self._server_thread.finished.connect(self._server_thread.deleteLater)
        self._server_thread.start()

    def stop_server(self):
        if self._server_worker is not None:
            self._server_worker.stop_server()
        
    def load_geometry_and_state(self):
        geometry = self._settings.get('mainwindow/geometry')
        state = self._settings.get('mainwindow/state')
        if isinstance(geometry, QByteArray) and self.restoreGeometry(geometry):
            if isinstance(state, QByteArray):
                self.restoreState(state)
            return
        self.resize(500, 700)
        self.center_window()        

    def save_geometry_and_state(self):
        self._settings.set('mainwindow/geometry', self.saveGeometry())
        self._settings.set('mainwindow/state', self.saveState())

    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.geometry().width()) / 2
        y = (screen.height() - self.geometry().height()) / 2
        self.move(int(x), int(y))