from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QGroupBox,
    QFileDialog, QSizePolicy, QScrollArea, QProgressBar
)
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QTimer, QRect

import os
import cv2
import numpy as np

# 模型目录路径 - 模型保存在 checkpoints 子目录
MODELS_DIR = "d:\\od\\ODPlatform\\models\\checkpoints"


class InferPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.selected_image = None
        self.selected_video = None
        self.is_camera_mode = False
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.model = None
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        title = QLabel("Inference")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #e2e8f0;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        config_group = QGroupBox("Inference Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                background-color: #252538;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                padding-top: 10px;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #93c5fd;
                font-weight: bold;
            }
        """)
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 200px;
            }
        """)
        self.load_models()
        config_layout.addWidget(self.model_combo)
        
        # 刷新模型列表按钮
        self.refresh_model_btn = QPushButton("Refresh")
        self.refresh_model_btn.clicked.connect(self.load_models)
        self.refresh_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d5c;
                color: #e2e8f0;
                border: 1px solid #52527a;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #52527a;
            }
        """)
        config_layout.addWidget(self.refresh_model_btn)
        
        config_layout.addWidget(QLabel("Confidence:"))
        self.confidence_edit = QLineEdit("0.25")
        self.confidence_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 6px 12px;
                width: 80px;
            }
        """)
        config_layout.addWidget(self.confidence_edit)
        
        config_layout.addStretch()
        layout.addWidget(config_group)
        
        input_group = QGroupBox("Input Source")
        input_group.setStyleSheet("""
            QGroupBox {
                background-color: #252538;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                padding-top: 10px;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #93c5fd;
                font-weight: bold;
            }
        """)
        input_layout = QHBoxLayout(input_group)
        
        self.image_btn = QPushButton("Select Image")
        self.image_btn.clicked.connect(self.select_image)
        self.image_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        input_layout.addWidget(self.image_btn)
        
        self.video_btn = QPushButton("Select Video")
        self.video_btn.clicked.connect(self.select_video)
        self.video_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d5c;
                color: #e2e8f0;
                border: 1px solid #52527a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #52527a;
            }
        """)
        input_layout.addWidget(self.video_btn)
        
        self.camera_btn = QPushButton("Camera")
        self.camera_btn.clicked.connect(self.select_camera)
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d5c;
                color: #e2e8f0;
                border: 1px solid #52527a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #52527a;
            }
        """)
        input_layout.addWidget(self.camera_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_inference)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f87171;
            }
            QPushButton:disabled {
                background-color: #434654;
            }
        """)
        input_layout.addWidget(self.stop_btn)
        
        input_layout.addStretch()
        layout.addWidget(input_group)
        
        content_layout = QHBoxLayout()
        
        self.image_frame = QFrame()
        self.image_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
            }
        """)
        self.image_layout = QVBoxLayout(self.image_frame)
        self.image_layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_label = QLabel("Select an image or camera to start")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #64748b;")
        self.image_layout.addWidget(self.image_label)
        
        content_layout.addWidget(self.image_frame)
        
        results_group = QGroupBox("Detection Results")
        results_group.setStyleSheet("""
            QGroupBox {
                background-color: #252538;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                padding-top: 10px;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #93c5fd;
                font-weight: bold;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        
        self.results_list = QScrollArea()
        self.results_list.setWidgetResizable(True)
        self.results_content = QWidget()
        self.results_content.setStyleSheet("background-color: #252538;")
        self.results_layout = QVBoxLayout(self.results_content)
        self.results_list.setWidget(self.results_content)
        results_layout.addWidget(self.results_list)
        
        content_layout.addWidget(results_group, 1)
        
        layout.addLayout(content_layout)
        
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Inference")
        self.run_btn.clicked.connect(self.run_inference)
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
            QPushButton:disabled {
                background-color: #434654;
            }
        """)
        button_layout.addWidget(self.run_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def refresh(self):
        self.load_models()
    
    def load_models(self):
        """扫描 models/checkpoints 目录下的所有 .pt 文件"""
        self.model_combo.clear()
        
        # 首先添加预训练模型
        default_models = ["yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt"]
        
        # 扫描本地模型目录
        local_models = []
        if os.path.exists(MODELS_DIR):
            local_models = sorted([f for f in os.listdir(MODELS_DIR) if f.lower().endswith('.pt')])
        
        # 合并所有模型（预训练模型 + 本地模型）
        all_models = default_models + local_models
        
        for model in all_models:
            self.model_combo.addItem(model)
    
    def get_model_path(self, model_name):
        """获取模型的完整路径"""
        # 默认模型直接返回文件名（由 ultralytics 自动下载）
        default_models = ["yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt"]
        if model_name in default_models:
            return model_name
        
        # 本地模型返回完整路径
        return os.path.join(MODELS_DIR, model_name)
    
    def clear_results(self):
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def select_image(self):
        self.stop_inference()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.selected_image = file_path
            self.selected_video = None
            self.is_camera_mode = False
            self.load_image(file_path)
            self.run_btn.setEnabled(True)
    
    def select_video(self):
        self.stop_inference()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if file_path:
            self.selected_video = file_path
            self.selected_image = None
            self.is_camera_mode = False
            self.image_label.setText(f"Video: {os.path.basename(file_path)}")
            self.run_btn.setEnabled(True)
    
    def select_camera(self):
        self.stop_inference()
        
        self.is_camera_mode = True
        self.selected_image = None
        self.selected_video = None
        self.run_btn.setEnabled(True)
        self.image_label.setText("Camera ready. Click Run Inference to start.")
    
    def load_image(self, path):
        image = QPixmap(path)
        if not image.isNull():
            image = image.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(image)
    
    def load_cv_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
    
    def run_inference(self):
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.clear_results()
        
        try:
            from ultralytics import YOLO
            model_name = self.model_combo.currentText()
            model_path = self.get_model_path(model_name)
            self.model = YOLO(model_path)
            
            if self.is_camera_mode:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    self.results_layout.addWidget(QLabel("Error: Could not open camera"))
                    self.stop_inference()
                    return
                self.timer.start(30)
                
            elif self.selected_image:
                results = self.model(self.selected_image, conf=float(self.confidence_edit.text()))
                self.process_results(results)
                
            elif self.selected_video:
                self.cap = cv2.VideoCapture(self.selected_video)
                if not self.cap.isOpened():
                    self.results_layout.addWidget(QLabel("Error: Could not open video"))
                    self.stop_inference()
                    return
                self.timer.start(30)
                
        except Exception as e:
            error_label = QLabel(f"Error: {str(e)}")
            error_label.setStyleSheet("color: #f87171;")
            self.results_layout.addWidget(error_label)
            self.stop_inference()
    
    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if self.model:
                    results = self.model(frame, conf=float(self.confidence_edit.text()))
                    annotated_frame = results[0].plot()
                    self.load_cv_image(annotated_frame)
                    self.show_results(results)
                else:
                    self.load_cv_image(frame)
    
    def process_results(self, results):
        for i, result in enumerate(results):
            annotated_frame = result.plot()
            self.load_cv_image(annotated_frame)
            self.show_results(results)
        self.stop_inference()
    
    def show_results(self, results):
        self.clear_results()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    names = result.names if hasattr(result, 'names') else {}
                    class_name = names.get(cls, f"Class {cls}")
                    label = f"{class_name}: {conf:.2f}"
                    label_widget = QLabel(label)
                    label_widget.setStyleSheet("color: #4ade80; padding: 4px;")
                    self.results_layout.addWidget(label_widget)
    
    def stop_inference(self):
        self.timer.stop()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if not self.selected_image and not self.selected_video:
            self.image_label.setText("Select an image, video, or camera to start")
            self.run_btn.setEnabled(False)
    
    def closeEvent(self, event):
        self.stop_inference()
        event.accept()