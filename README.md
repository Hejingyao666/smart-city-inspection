# 智慧城市巡检 · 端到端目标检测平台

面向智慧城市巡检场景的端到端目标检测平台，包含数据采集、推理加速、结果可视化与模型训练评估的完整链路。

## ✨ 核心功能

- 🎯 **推理模块工程化**：设计图像帧预处理流水线（缩放/归一化/格式转换），实现 NMS、坐标映射、置信度过滤等后处理
- ⚡ **性能优化**：通过批量推理、循环逻辑优化及内存复用，帧率从 **25 FPS 提升至 60 FPS**（提升 140%）
- 🖼️ **多源输入支持**：兼容视频流、图像批量数据、摄像头实时采集
- 📊 **训练评估**：在 RSOD 公开数据集上完成测试，mAP@0.5 = **94.8%**
- 📝 **配置化部署**：沉淀推理部署脚本与参数配置模板，支持快速迁移至新场景

## 🛠️ 技术栈

| 分类 | 技术 |
|------|------|
| **深度学习框架** | PyTorch |
| **目标检测** | YOLO 系列 / 自定义检测模型 |
| **推理优化** | 批量推理、内存复用、流水线并行 |
| **后处理** | NMS、坐标映射、置信度过滤 |
| **可视化** | OpenCV、Matplotlib |
| **工具** | Docker、Git、Linux |

## 📁 项目结构
smart-city-inspection/
├── apps/
│ └── platform/ # 核心平台代码
│ ├── src/odp_platform/
│ │ ├── data_validation/ # 数据校验模块
│ │ ├── frame_source/ # 多源输入（摄像头/视频/图像）
│ │ ├── inference/ # 推理引擎（pipeline、hooks、overlay）
│ │ ├── runtime_config/ # 运行时配置管理
│ │ ├── training/ # 训练相关
│ │ └── visualization/ # 结果可视化
│ └── tests/ # 单元测试
├── models/
│ └── checkpoints/ # 模型权重文件
├── packages/
│ └── shared-schemas/ # 共享数据 schema
├── scripts/ # 工具脚本
└── .gitignore

text

## 🚀 快速开始

### 环境要求

- Python 3.8+
- CUDA 11.0+（推荐 GPU 推理）
- PyTorch 1.10+

### 1. 克隆项目

```bash
git clone https://github.com/Hejingyao666/smart-city-inspection.git
cd smart-city-inspection
2. 安装依赖
bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install torch torchvision opencv-python numpy matplotlib
# 如有 requirements.txt，使用 pip install -r requirements.txt
3. 下载模型权重
将训练好的模型权重文件放入 models/checkpoints/ 目录。

4. 运行推理
bash
# 视频流推理示例
python apps/platform/src/odp_platform/inference/service.py \
    --source /path/to/video.mp4 \
    --weights models/checkpoints/model.pth \
    --conf-thres 0.5

# 图像批量推理
python apps/platform/src/odp_platform/inference/pipeline.py \
    --source /path/to/images/ \
    --weights models/checkpoints/model.pth \
    --batch-size 8
5. 配置化部署
通过运行时配置文件（runtime_config/）调整推理参数，无需修改代码即可适配不同场景：

yaml
# config.yaml 示例
model:
  weights: models/checkpoints/model.pth
  conf_threshold: 0.5
  iou_threshold: 0.45

input:
  source: video
  path: /path/to/video.mp4
  fps: 30

output:
  save_dir: outputs/
  visualization: true
📊 性能指标
指标	数据
原始帧率	25 FPS
优化后帧率	60 FPS
性能提升	140%
RSOD mAP@0.5	94.8%
📝 项目亮点
工程化推理模块：完整的预处理 → 推理 → 后处理流水线，支持多种输入源

显著的性能优化：通过批量推理与内存复用，帧率提升 140%

配置化部署：运行时配置管理，支持快速迁移至新场景

完整的训练评估链路：从数据标注到模型验证的闭环# 项目说明文件
