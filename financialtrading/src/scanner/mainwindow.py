import os
import numpy as np
from pathlib import Path
from PySide6.QtCore import Qt, QByteArray, QThread
from PySide6.QtWidgets import QMainWindow, QWidget, QStyle, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QGuiApplication, QAction
from scanner.settings import Settings
from scanner.flaskserverworker import FlaskServerWorker
from scanner.scanner import Scanner

DATA_DIR = str(Path(__file__).resolve().parent)
DATA_TOKENINFO_FILE = os.path.join(DATA_DIR, 'data/tokeninfo.json')


class MainWindow(QMainWindow):
    def __init__(self, bundle_identifier, app_name, app_icon):
        super(MainWindow, self).__init__()
        self._settings = Settings(bundle_identifier, app_name)
        self._app_icon = app_icon
        self._toggle_server_button = QPushButton('Start Oauth 2.0 server to obtain new access token')
        self._toggle_server_button.clicked.connect(self.handle_toggle_server_button)
        self._ema_period_spinbox = QSpinBox(self, minimum=1, maximum=100, value=20)
        self._slope_lookback_spinbox = QSpinBox(self, minimum=0, maximum=100, value=5)
        self._min_slope_pct_spinbox = QSpinBox(self, minimum=0, maximum=100, value=2)
        self._price_min_spinbox = QSpinBox(self, minimum=0, maximum=200, value=10)
        self._price_max_spinbox = QSpinBox(self, minimum=0, maximum=200, value=100)
        self._start_scan_button = QPushButton('Start scanning daily charts for stocks and ETFs')
        self._start_scan_button.setStyleSheet('background-color: blue; color: white; font-weight: bold;')
        self._start_scan_button.clicked.connect(self.handle_start_scan_button)
        self._etfs_table = QTableWidget()
        self._stocks_table = QTableWidget()
        self._server_thread = None
        self._server_worker = None
        self._server_running = False
        self._scanner = None
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
        layout.addWidget(QLabel('EMA period:'))
        layout.addWidget(self._ema_period_spinbox)
        layout.addWidget(QLabel('Minimum slope percentage:'))
        layout.addWidget(self._min_slope_pct_spinbox)
        layout.addWidget(QLabel('Slope lookback nr. days:'))
        layout.addWidget(self._slope_lookback_spinbox)
        layout.addWidget(QLabel('Price range:'))
        price_range_layout = QHBoxLayout()
        price_range_layout.addWidget(self._price_min_spinbox)
        price_range_layout.addWidget(self._price_max_spinbox)
        layout.addLayout(price_range_layout)
        layout.addWidget(self._start_scan_button)
        layout.addWidget(QLabel('Candidate ETFs:'))
        layout.addWidget(self._etfs_table)
        layout.addWidget(QLabel('Candidate stocks:'))
        layout.addWidget(self._stocks_table)
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

    def handle_start_scan_button(self):
        self._scanner = Scanner(
            self._ema_period_spinbox.value(),
            self._slope_lookback_spinbox.value(),
            self._min_slope_pct_spinbox.value(),
            (self._price_min_spinbox.value(), self._price_max_spinbox.value()),
        )
        rows_etfs, rows_stocks = self._scanner.run()
        self.show_etfs_and_stocks(rows_etfs, rows_stocks)

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
        self._server_running = False

    def show_etfs_and_stocks(self, rows_etfs, rows_stocks):
        self.show_table(rows_etfs, self._etfs_table)
        self.show_table(rows_stocks, self._stocks_table)

    def show_table(self, rows, table):
        headers = list(rows[0].keys())
        table.setRowCount(len(rows))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, key in enumerate(headers):
                value = row.get(key, "")
                text = self.format_value(value)
                item = QTableWidgetItem(text)
                # Optional: align numbers nicely
                if isinstance(value, (int, float, np.integer, np.floating)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, item)
        table.resizeColumnsToContents()

    @staticmethod
    def format_value(value):
        if isinstance(value, (np.bool_, bool)):
            return "True" if bool(value) else "False"
        if isinstance(value, (np.integer, int)):
            return str(int(value))
        if isinstance(value, (np.floating, float)):
            return f"{float(value):.3f}"
        return str(value)
        
    def load_geometry_and_state(self):
        geometry = self._settings.get('mainwindow/geometry')
        state = self._settings.get('mainwindow/state')
        if isinstance(geometry, QByteArray) and self.restoreGeometry(geometry):
            if isinstance(state, QByteArray):
                self.restoreState(state)
            return
        self.resize(500, 1000)
        self.center_window()        

    def save_geometry_and_state(self):
        self._settings.set('mainwindow/geometry', self.saveGeometry())
        self._settings.set('mainwindow/state', self.saveState())

    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.geometry().width()) / 2
        y = (screen.height() - self.geometry().height()) / 2
        self.move(int(x), int(y))