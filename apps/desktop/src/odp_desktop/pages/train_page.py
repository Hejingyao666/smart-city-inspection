from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import subprocess
import os
import time
import re


class TrainWorker(QThread):
    log_update = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, cmd, cwd, env):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                universal_newlines=False
            )

            while self.process.poll() is None:
                try:
                    chunk = self.process.stdout.read(4096)
                    if chunk:
                        try:
                            text = chunk.decode('utf-8', errors='replace')
                        except:
                            text = chunk.decode('gbk', errors='replace')
                        
                        text = text.replace('\r', '\n')
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line:
                                self.log_update.emit(line)
                except Exception as e:
                    self.log_update.emit(f"Error reading output: {str(e)}")
                    time.sleep(0.1)

            try:
                remaining = self.process.stdout.read(4096)
                if remaining:
                    try:
                        text = remaining.decode('utf-8', errors='replace')
                    except:
                        text = remaining.decode('gbk', errors='replace')
                    self.log_update.emit(text.strip())
            except:
                pass

            self.finished.emit(self.process.returncode)
        except Exception as e:
            self.log_update.emit(f"Error starting training: {str(e)}")
            self.finished.emit(-1)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()


class TrainPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.training_thread = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        config_group = QGroupBox("Training Configuration")
        config_layout = QGridLayout()
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(15, 15, 15, 15)

        row = 0
        
        self.dataset_label = QLabel("Dataset:")
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems(["RSOD", "DIOR"])
        config_layout.addWidget(self.dataset_label, row, 0)
        config_layout.addWidget(self.dataset_combo, row, 1)
        row += 1

        self.model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt"])
        config_layout.addWidget(self.model_label, row, 0)
        config_layout.addWidget(self.model_combo, row, 1)
        row += 1

        self.epochs_label = QLabel("Epochs:")
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(70)
        config_layout.addWidget(self.epochs_label, row, 0)
        config_layout.addWidget(self.epochs_spin, row, 1)
        row += 1

        self.batch_label = QLabel("Batch Size:")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 128)
        self.batch_spin.setValue(16)
        config_layout.addWidget(self.batch_label, row, 0)
        config_layout.addWidget(self.batch_spin, row, 1)
        row += 1

        self.lr_label = QLabel("Learning Rate:")
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.1)
        self.lr_spin.setValue(0.01)
        self.lr_spin.setDecimals(4)
        config_layout.addWidget(self.lr_label, row, 0)
        config_layout.addWidget(self.lr_spin, row, 1)
        row += 1

        self.device_label = QLabel("Device:")
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "0", "1"])
        config_layout.addWidget(self.device_label, row, 0)
        config_layout.addWidget(self.device_combo, row, 1)
        row += 1

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        log_group = QGroupBox("Training Log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(15, 15, 15, 15)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(500)  # 增大最小高度
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        button_layout = QHBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
        """)
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        
        self.start_btn = QPushButton("Start Training")
        self.start_btn.clicked.connect(self.start_training)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #4b5563;
            }
        """)

        self.pause_btn = QPushButton("Stop")
        self.pause_btn.clicked.connect(self.pause_training)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #2d2d44;
                color: #6b7280;
            }
        """)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #252538;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                color: #93c5fd;
                padding-left: 10px;
                padding-right: 10px;
            }
            QLabel {
                color: #94a3b8;
                font-size: 13px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                min-width: 200px;
            }
            QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2a2a42;
            }
            QProgressBar {
                background-color: #1e1e2e;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                height: 25px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 6px;
            }
        """)

    def start_training(self):
        dataset = self.dataset_combo.currentText()
        model = self.model_combo.currentText()
        epochs = self.epochs_spin.value()
        batch_size = self.batch_spin.value()
        lr = self.lr_spin.value()
        device = self.device_combo.currentText()

        train_yaml_path = "d:\\od\\ODPlatform\\apps\\platform\\configs\\runtime\\train.yaml"
        data_yaml_path = f"d:\\od\\ODPlatform\\apps\\platform\\configs\\datasets\\{dataset.lower()}.yaml"
        cmd = [
            "python", "-m", "odp_platform.cli.train_model",
            "--yaml", train_yaml_path,
            "--data", data_yaml_path,
            "--model", model,
            "--epochs", str(epochs),
            "--batch", str(batch_size),
            "--lr0", str(lr),
            "--device", device,
            "--no-pre-validate"
        ]

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = "d:\\od\\ODPlatform\\apps\\platform\\src;d:\\od\\ODPlatform\\apps\\desktop\\src"
            env["PATH"] = "D:\\miniconda\\envs\\odplatform-gpu\\Scripts;" + env["PATH"]
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["LC_ALL"] = "en_US.UTF-8"
            env["LANG"] = "en_US.UTF-8"

            self.training_thread = TrainWorker(cmd, "d:\\od\\ODPlatform\\apps\\platform", env)
            self.training_thread.log_update.connect(self.append_log)
            self.training_thread.finished.connect(self.on_training_finished)

            self.log_text.clear()
            self.status_label.setText("Training...")
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)

            self.training_thread.start()
        except Exception as e:
            self.log_text.append(f"Error starting training: {str(e)}")

    def pause_training(self):
        if self.training_thread:
            self.training_thread.stop()
            self.status_label.setText("Stopping...")

    def append_log(self, text):
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def on_training_finished(self, return_code):
        if return_code == 0:
            self.log_text.append("\n" + "="*60)
            self.log_text.append("Training completed successfully!")
            self.status_label.setText("Completed")
        elif return_code == 130:
            self.log_text.append("\n" + "="*60)
            self.log_text.append("Training interrupted by user")
            self.status_label.setText("Interrupted")
        else:
            self.log_text.append("\n" + "="*60)
            self.log_text.append(f"Training failed with exit code {return_code}")
            self.status_label.setText("Failed")

        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def refresh(self):
        pass