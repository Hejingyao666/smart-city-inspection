from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QToolButton, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from odp_desktop.pages.train_page import TrainPage
from odp_desktop.pages.infer_page import InferPage
from odp_desktop.pages.split_page import SplitPage


class Sidebar(QWidget):
    page_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #252538;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 20, 20, 20)
        
        logo_label = QLabel("ODPlatform")
        logo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #818cf8;")
        logo_layout.addWidget(logo_label)
        
        sub_label = QLabel("AI Training Platform")
        sub_label.setFont(QFont("Segoe UI", 10))
        sub_label.setStyleSheet("color: #94a3b8;")
        logo_layout.addWidget(sub_label)
        
        layout.addWidget(logo_frame)
        
        self.buttons = []
        nav_items = [
            ("Train", "train", "Training"),
            ("Split", "split", "Dataset Split"),
            ("Infer", "infer", "Inference")
        ]
        
        for text, page_id, tooltip in nav_items:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(20, 20))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(45)
            btn.setStyleSheet("""
                QToolButton {
                    background-color: #1e1e2e;
                    color: #cbd5e1;
                    padding-left: 20px;
                    text-align: left;
                    border: none;
                    font-size: 13px;
                }
                QToolButton:hover {
                    background-color: #374151;
                }
                QToolButton:pressed, QToolButton:checked {
                    background-color: #6366f1;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, pid=page_id: self.on_button_click(pid))
            self.buttons.append((btn, page_id))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedWidth(180)
        self.setStyleSheet("background-color: #1e1e2e;")
    
    def on_button_click(self, page_id):
        for btn, pid in self.buttons:
            btn.setChecked(pid == page_id)
        self.page_changed.emit(page_id)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ODPlatform")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("background-color: #181825;")
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #181825;")
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.change_page)
        layout.addWidget(self.sidebar)
        
        self.content_area = QFrame()
        self.content_area.setStyleSheet("background-color: #1f1f2e;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_area)
        
        self.pages = {}
        self.pages["train"] = TrainPage()
        self.pages["split"] = SplitPage()
        self.pages["infer"] = InferPage()
        
        for page in self.pages.values():
            page.hide()
            self.content_layout.addWidget(page)
        
        self.change_page("train")
    
    def change_page(self, page_id):
        for pid, page in self.pages.items():
            page.hide()
        
        if page_id in self.pages:
            self.pages[page_id].show()
            self.pages[page_id].refresh()
        
        for btn, pid in self.sidebar.buttons:
            btn.setChecked(pid == page_id)