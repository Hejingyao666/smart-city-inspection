from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import subprocess
import os

# 默认划分比例
DEFAULT_TRAIN_RATE = 0.8
DEFAULT_VAL_RATE = 0.1


class SplitWorker(QThread):
    log_update = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, dataset_name, annotation_format, cwd, env):
        super().__init__()
        self.dataset_name = dataset_name
        self.annotation_format = annotation_format
        self.cwd = cwd
        self.env = env

    def run(self):
        try:
            cmd = [
                "D:\\miniconda\\envs\\odplatform-gpu\\python.exe", "-m", "odp_platform.cli.transform_data",
                "--dataset", self.dataset_name,
                "--format", self.annotation_format,
                "--train-rate", str(DEFAULT_TRAIN_RATE),
                "--val-rate", str(DEFAULT_VAL_RATE)
            ]
            
            test_rate = 1.0 - DEFAULT_TRAIN_RATE - DEFAULT_VAL_RATE
            self.log_update.emit(f"开始划分数据集: {self.dataset_name}")
            self.log_update.emit(f"划分比例: 训练集={DEFAULT_TRAIN_RATE:.1%}, 验证集={DEFAULT_VAL_RATE:.1%}, 测试集={test_rate:.1%}")
            self.log_update.emit(f"执行命令: {' '.join(cmd)}")
            self.log_update.emit(f"工作目录: {self.cwd}")
            self.log_update.emit("-" * 60)
            
            process = subprocess.Popen(
                cmd,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=4096,
                universal_newlines=False
            )
            
            stdout, stderr = process.communicate()
            
            if stdout:
                try:
                    text = stdout.decode('utf-8', errors='replace')
                except:
                    text = stdout.decode('gbk', errors='replace')
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        self.log_update.emit(line)
            
            if stderr:
                try:
                    text = stderr.decode('utf-8', errors='replace')
                except:
                    text = stderr.decode('gbk', errors='replace')
                if text.strip():
                    self.log_update.emit(f"STDERR: {text.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                self.log_update.emit("-" * 60)
                self.log_update.emit("数据集划分完成！")
                self.finished.emit(0)
            else:
                self.log_update.emit(f"数据集划分失败，退出码: {process.returncode}")
                self.finished.emit(process.returncode)
                
        except Exception as e:
            self.log_update.emit(f"错误: {str(e)}")
            self.finished.emit(-1)


class SplitPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.split_thread = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        header = QLabel("Dataset Split")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(header)

        # 数据集选择组
        select_group = QGroupBox("Select Dataset")
        select_group.setStyleSheet(self._get_group_style())
        select_layout = QGridLayout(select_group)
        select_layout.setSpacing(12)

        # 数据集选择
        row = 0
        select_layout.addWidget(QLabel("Dataset Name:"), row, 0)
        self.dataset_combo = QComboBox()
        self.dataset_combo.setMinimumWidth(400)
        self.dataset_combo.setStyleSheet(self._get_combo_style())
        self.dataset_combo.currentIndexChanged.connect(self.on_dataset_selected)
        select_layout.addWidget(self.dataset_combo, row, 1)
        row += 1

        # 图像数量
        select_layout.addWidget(QLabel("Total Images:"), row, 0)
        self.total_images_label = QLabel("N/A")
        self.total_images_label.setStyleSheet("color: #94a3b8;")
        select_layout.addWidget(self.total_images_label, row, 1)
        row += 1

        # 标注格式选择
        select_layout.addWidget(QLabel("Annotation Format:"), row, 0)
        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(self._get_combo_style())
        self.format_combo.addItems(["pascal_voc", "coco", "yolo"])
        self.format_combo.setCurrentText("pascal_voc")
        select_layout.addWidget(self.format_combo, row, 1)
        row += 1

        # 划分按钮
        self.split_btn = QPushButton("Start Split")
        self.split_btn.clicked.connect(self.start_split)
        self.split_btn.setStyleSheet(self._get_button_style("#22c55e"))
        select_layout.addWidget(self.split_btn, row, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addWidget(select_group)

        # 日志输出组
        log_group = QGroupBox("Split Log")
        log_group.setStyleSheet(self._get_group_style())
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 10, 10, 10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        self.setLayout(layout)

        # 初始化
        self.refresh_datasets()

    def _get_group_style(self):
        return """
            QGroupBox {
                background-color: #252538;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e2e8f0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #93c5fd;
            }
            QLabel {
                color: #94a3b8;
                font-size: 13px;
            }
        """

    def _get_combo_style(self):
        return """
            QComboBox {
                background-color: #1e1e2e;
                color: #e2e8f0;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #94a3b8;
                margin-right: 10px;
            }
        """

    def _get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:disabled {{
                background-color: #4b5563;
                color: #9ca3af;
            }}
        """

    def refresh(self):
        self.refresh_datasets()

    def refresh_datasets(self):
        raw_data_dir = "d:\\od\\ODPlatform\\data\\raw"
        
        self.dataset_combo.clear()
        
        if os.path.exists(raw_data_dir):
            datasets = [d for d in os.listdir(raw_data_dir) 
                       if os.path.isdir(os.path.join(raw_data_dir, d))]
            self.dataset_combo.addItems(sorted(datasets))
            
            if datasets:
                self.log_text.append(f"发现 {len(datasets)} 个原始数据集")
                self.dataset_combo.currentIndexChanged.emit(0)
        else:
            self.log_text.append(f"原始数据目录不存在: {raw_data_dir}")

    def on_dataset_selected(self, index):
        dataset_name = self.dataset_combo.currentText()
        
        if not dataset_name:
            self.total_images_label.setText("N/A")
            self.split_btn.setText("Start Split")
            self.split_btn.setStyleSheet(self._get_button_style("#22c55e"))
            return
        
        raw_path = f"d:\\od\\ODPlatform\\data\\raw\\{dataset_name}"
        
        # 统计图像数量
        total_images = 0
        if os.path.exists(raw_path):
            for root, dirs, files in os.walk(raw_path):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                        total_images += 1
        
        self.total_images_label.setText(f"{total_images} images")
        
        # 检查是否已划分
        is_split = False
        output_path = f"d:\\od\\ODPlatform\\data\\{dataset_name}"
        if os.path.exists(output_path):
            has_train = os.path.exists(os.path.join(output_path, "train"))
            has_val = os.path.exists(os.path.join(output_path, "val"))
            has_test = os.path.exists(os.path.join(output_path, "test"))
            has_yaml = os.path.exists(os.path.join(output_path, f"{dataset_name.lower()}.yaml"))
            if has_train and has_val and has_test and has_yaml:
                is_split = True
        
        if is_split:
            self.split_btn.setText("Resplit Dataset")
            self.split_btn.setStyleSheet(self._get_button_style("#f59e0b"))
        else:
            self.split_btn.setText("Start Split")
            self.split_btn.setStyleSheet(self._get_button_style("#22c55e"))

    def start_split(self):
        dataset_name = self.dataset_combo.currentText()
        if not dataset_name:
            QMessageBox.warning(self, "Warning", "请先选择一个数据集")
            return
        
        test_rate = 1.0 - DEFAULT_TRAIN_RATE - DEFAULT_VAL_RATE
        
        self.log_text.clear()
        self.log_text.append(f"开始划分数据集: {dataset_name}")
        self.log_text.append(f"训练集: {DEFAULT_TRAIN_RATE:.1%}, 验证集: {DEFAULT_VAL_RATE:.1%}, 测试集: {test_rate:.1%}")
        self.log_text.append("-" * 60)
        
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = "d:\\od\\ODPlatform\\apps\\platform\\src;d:\\od\\ODPlatform\\apps\\desktop\\src"
            env["PATH"] = "D:\\miniconda\\envs\\odplatform-gpu\\Scripts;" + env["PATH"]
            env["PYTHONUNBUFFERED"] = "1"
            env["LC_ALL"] = "en_US.UTF-8"
            env["LANG"] = "en_US.UTF-8"
            
            annotation_format = self.format_combo.currentText()
            
            self.split_thread = SplitWorker(
                dataset_name=dataset_name,
                annotation_format=annotation_format,
                cwd="d:\\od\\ODPlatform\\apps\\platform",
                env=env
            )
            self.split_thread.log_update.connect(self.append_log)
            self.split_thread.finished.connect(self.on_split_finished)
            self.split_thread.start()
            
            self.split_btn.setEnabled(False)
            self.dataset_combo.setEnabled(False)
            
        except Exception as e:
            self.log_text.append(f"启动失败: {str(e)}")

    def append_log(self, text):
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def on_split_finished(self, return_code):
        self.split_btn.setEnabled(True)
        self.dataset_combo.setEnabled(True)
        
        if return_code == 0:
            self.log_text.append("\n" + "=" * 60)
            self.log_text.append("✓ 数据集划分成功完成！")
            self.log_text.append("=" * 60)
            QMessageBox.information(self, "Success", "数据集划分成功完成！\n\n您可以在训练页面使用该数据集。")
        else:
            self.log_text.append(f"\n✗ 数据集划分失败，退出码: {return_code}")
            QMessageBox.critical(self, "Error", f"数据集划分失败，退出码: {return_code}")
