#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
frame_source + 美化模块 联合测试

链路: frame_source 取帧 → YOLO 推理 → BeautifyVisualizer 美化绘制 → cv2.imshow

用法:
    # 摄像头 (默认, 需要 YOLO 模型)
    python 07-frame_source+美化测试.py

    # Demo 模式: 无模型, 用随机模拟检测框 (立即看美化效果)
    python 07-frame_source+美化测试.py --demo

    # 静态图片 + Demo: 不需要摄像头
    python 07-frame_source+美化测试.py --demo --source frame_000042.png

    # 视频文件
    python 07-frame_source+美化测试.py --source /path/to/video.mp4

    # 单张图片 (逐帧模式: 反复显示同一张)
    python 07-frame_source+美化测试.py --source /path/to/image.jpg

按键:
    ESC / q  — 退出
    s        — 截图保存到 screenshots_beautify/ 目录
    m        — 切换中/英文标签映射
    d        — 切换是否显示检测框 (纯画面 / 带框)
    f        — 切换是否显示 FPS 信息面板

依赖:
    - ultralytics (YOLO) — --demo 模式不需要
    - opencv-python
    - visualization 模块 (美化绘制)
    - odp_platform.frame_source 模块 (统一帧输入)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# ── 项目路径 ────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent  # ODPlatform/
_SRC = _PROJECT_ROOT / "apps" / "platform" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from odp_platform.frame_source import CameraConfig, create_frame_source, create_threaded_source
from odp_platform.frame_source.core.types import Frame
from odp_platform.visualization import BeautifyVisualizer, Detection, DrawStyle


# ═══════════════════════════════════════════════════════════════
# 配置区
# ═══════════════════════════════════════════════════════════════

# 模型路径 — None 则自动查找
MODEL_PATH: Optional[Path] = (
    Path(__file__).resolve().parent
    / "train3-20250704-165500-yolo11n-best.pt"
)

# 摄像头配置
CAMERA_ID = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 90
CAMERA_BACKEND = "msmf"

# 线程化源预热帧数
THREAD_WARMUP = 30

# YOLO 推理参数
CONF_THRESHOLD = 0.25   # 置信度阈值
DEVICE = 0              # 推理设备: 0=GPU, "cpu"=CPU

# 显示配置
DISPLAY_WINDOW = "BeautifyVisualizer + frame_source"
DISPLAY_INTERVAL = 1.0 / 30  # 显示帧率上限

# 截图保存目录
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots_beautify"

# ── 常用中英文标签映射 (COCO 80 类 + 常见自训练类) ────────
# 模型自有类别会从 model.names 自动提取；在此字典中的会被映射为中文。
BUILTIN_LABEL_MAPPING: Dict[str, str] = {
    # COCO 常见类
    "person":        "人员",
    "head": "没带安全帽",
    "safety_helmet":   "佩戴安全帽",
    "ordinary_clothes": "普通衣服",
    "reflective_vest": "反光衣",
}

# ── 颜色映射 (BGR) ──────────────────────────────────────────
# 为每个类别预设颜色；不在字典中的类别使用 default_color
BUILTIN_COLOR_MAPPING: Dict[str, Tuple[int, int, int]] = {
    "person":    (0, 255, 0),     # 绿
    "head":       (255, 100, 0),   # 橙
    "safety_helmet":     (255, 0, 0),     # 蓝
    "ordinary_clothe":       (255, 0, 255),   # 紫
    "reflective_vest":(0, 200, 255),   # 金
}


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def load_model(model_path: Path, device: int | str = 0):
    """加载 YOLO 模型并返回 (model, class_names)。"""
    from ultralytics import YOLO

    if not model_path.exists():
        raise FileNotFoundError(f"模型不存在: {model_path}")

    print(f"[模型] 加载: {model_path}")
    model = YOLO(str(model_path))

    # 获取类别名
    class_names: Dict[int, str] = model.names if hasattr(model, "names") else {}

    # GPU 预热
    try:
        import torch
        cuda_ok = (str(device) != "cpu") and torch.cuda.is_available()
    except ImportError:
        cuda_ok = False

    if cuda_ok:
        print(f"[模型] Device: CUDA:{device}")
        dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
        print("[模型] GPU 预热 (CUDA kernel 编译)...", end=" ", flush=True)
        t0 = time.perf_counter()
        model(dummy, verbose=False)
        print(f"完成 ({time.perf_counter() - t0:.2f}s)")
    else:
        print("[模型] Device: CPU")

    print(f"[模型] 类别数: {len(class_names)}")
    if class_names:
        sample = list(class_names.values())[:8]
        print(f"[模型] 前几类: {sample}{'...' if len(class_names) > 8 else ''}")

    return model, class_names


def build_label_mapping(class_names: Dict[int, str]) -> Dict[str, str]:
    """根据模型类别名 + 内置字典,生成标签映射。

    模型中的类别如果在 BUILTIN_LABEL_MAPPING 中有对应中文,
    则使用中文;否则保留英文原名。
    """
    mapping: Dict[str, str] = {}
    for idx, name in class_names.items():
        name_lower = name.strip().lower()
        if name_lower in BUILTIN_LABEL_MAPPING:
            mapping[name] = BUILTIN_LABEL_MAPPING[name_lower]
        elif name in BUILTIN_LABEL_MAPPING:
            mapping[name] = BUILTIN_LABEL_MAPPING[name]
        # 否则不加入 mapping,保留英文
    return mapping


def build_color_mapping(class_names: Dict[int, str]) -> Dict[str, Tuple[int, int, int]]:
    """根据模型类别名 + 内置颜色,生成颜色映射。

    不在 BUILTIN_COLOR_MAPPING 中的类别,自动分配颜色。
    """
    import colorsys

    mapping: Dict[str, Tuple[int, int, int]] = {}
    auto_idx = 0
    for idx, name in class_names.items():
        name_lower = name.strip().lower()
        if name_lower in BUILTIN_COLOR_MAPPING:
            mapping[name] = BUILTIN_COLOR_MAPPING[name_lower]
        elif name in BUILTIN_COLOR_MAPPING:
            mapping[name] = BUILTIN_COLOR_MAPPING[name]
        else:
            # 自动生成 HSV 均匀分布的颜色 → BGR
            hue = (auto_idx * 0.618033988749895) % 1.0  # 黄金比例分布
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            mapping[name] = (int(b * 255), int(g * 255), int(r * 255))
            auto_idx += 1
    return mapping


def yolo_inference(
    model,
    frame: np.ndarray,
    conf: float = 0.25,
    device: int | str = 0,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """YOLO 推理, 返回 (boxes_xyxy, confidences, labels)。"""
    results = model(frame, verbose=False, conf=conf, device=device)
    if results[0].boxes is None:
        return (
            np.empty((0, 4), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            [],
        )
    boxes = results[0].boxes.xyxy.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()
    cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
    labels = [model.names.get(int(c), f"cls_{c}") for c in cls_ids]
    return boxes, confs, labels


def generate_mock_detections(
    frame: np.ndarray,
    class_names: Dict[int, str],
    num_dets: int = 6,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """生成随机模拟检测结果 (Demo 模式, 不需要 YOLO 模型)。

    根据画面尺寸随机生成不同位置/大小的检测框,
    让用户可以立即看到美化效果。
    """
    h, w = frame.shape[:2]
    rng = np.random.RandomState(42)  # 固定种子, 可复现

    num_classes = max(len(class_names), 1)
    labels_list = list(class_names.values()) if class_names else ["object"]

    boxes = []
    confs = []
    labels = []

    for i in range(num_dets):
        # 随机框大小 (占画面 10% ~ 40%)
        bw = int(w * rng.uniform(0.10, 0.35))
        bh = int(h * rng.uniform(0.10, 0.40))
        # 随机位置
        x1 = rng.randint(0, max(1, w - bw - 1))
        y1 = rng.randint(0, max(1, h - bh - 1))
        x2 = min(x1 + bw, w - 1)
        y2 = min(y1 + bh, h - 1)

        boxes.append([float(x1), float(y1), float(x2), float(y2)])
        confs.append(float(rng.uniform(0.60, 0.99)))
        # 轮流使用不同类别
        cls_id = i % num_classes
        labels.append(labels_list[cls_id])

    return (
        np.array(boxes, dtype=np.float32),
        np.array(confs, dtype=np.float32),
        labels,
    )


def draw_osd(
    image: np.ndarray,
    fps: float,
    frame_idx: int,
    use_mapping: bool,
    show_detections: bool,
    resolution: Tuple[int, int],
    infer_ms: float,
    num_dets: int,
    model_name: str = "",
) -> np.ndarray:
    """在画面叠加 OSD 信息栏 (半透明底栏 + 文字)。"""
    h, w = image.shape[:2]
    bar_h = 80

    # 半透明底栏
    overlay = image.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (20, 20, 20), -1)
    image = cv2.addWeighted(image, 0.55, overlay, 0.45, 0)

    # 分隔线
    cv2.line(image, (0, h - bar_h), (w, h - bar_h), (60, 60, 60), 2)

    row1_y = h - bar_h + 22
    row2_y = h - bar_h + 50

    font = cv2.FONT_HERSHEY_SIMPLEX
    color_green = (0, 255, 0)
    color_white = (220, 220, 220)
    color_yellow = (0, 220, 255)
    color_cyan = (255, 200, 0)

    # 第一行: FPS | 推理耗时 | 帧号
    cv2.putText(image, f"FPS: {fps:.1f}", (14, row1_y),
                font, 0.55, color_green, 2)
    cv2.putText(image, f"Infer: {infer_ms:.0f}ms", (130, row1_y),
                font, 0.50, color_yellow, 1)
    cv2.putText(image, f"Frame: #{frame_idx}", (260, row1_y),
                font, 0.50, color_white, 1)
    cv2.putText(image, f"Dets: {num_dets}", (400, row1_y),
                font, 0.50, color_cyan, 1)

    # 第二行: 状态信息
    status_parts = []
    status_parts.append(f"{resolution[0]}x{resolution[1]}")
    status_parts.append(f"Lang: {'CN' if use_mapping else 'EN'}")
    status_parts.append(f"Box: {'ON' if show_detections else 'OFF'}")
    if model_name:
        status_parts.append(str(model_name)[:30])

    status_text = " | ".join(status_parts)
    cv2.putText(image, status_text, (14, row2_y),
                font, 0.45, (160, 160, 160), 1)

    # 右下角按键提示
    hints = "q:退出  s:截图  m:中/英  d:框开关  f:FPS开关"
    (tw, _), _ = cv2.getTextSize(hints, font, 0.40, 1)
    cv2.putText(image, hints, (w - tw - 14, row2_y),
                font, 0.40, (120, 120, 120), 1)

    return image


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="frame_source + 美化模块 联合测试"
    )
    parser.add_argument(
        "--source", "-s", type=str, default="0",
        help='输入源: "0"=摄像头, 或视频/图片路径 (默认: "0")',
    )
    parser.add_argument(
        "--model", "-m", type=str, default=None,
        help="YOLO 模型路径 (默认: 自动查找同目录下 .pt 文件)",
    )
    parser.add_argument(
        "--conf", type=float, default=CONF_THRESHOLD,
        help=f"置信度阈值 (默认: {CONF_THRESHOLD})",
    )
    parser.add_argument(
        "--device", type=str, default=str(DEVICE),
        help='推理设备 (默认: 0=GPU, "cpu"=CPU)',
    )
    parser.add_argument(
        "--warmup", type=int, default=THREAD_WARMUP,
        help=f"线程化源预热帧数 (默认: {THREAD_WARMUP})",
    )
    parser.add_argument(
        "--no-thread", action="store_true",
        help="不使用线程化源 (同步采集)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Demo 模式: 生成随机模拟检测框, 不需要 YOLO 模型, 立即看美化效果",
    )
    args = parser.parse_args()

    # ── 1. 加载模型 / Demo 模式 ───────────────────────────────
    if args.demo:
        # Demo 模式: 使用 COCO 示例类别, 不需要 YOLO 模型
        print("[Demo] 无需模型, 使用内置模拟类别 + 随机检测框")
        model = None
        # 使用 BUILTIN_LABEL_MAPPING 中前 10 个作为演示类别
        demo_labels = [
            "person", "car", "dog", "cat", "bicycle",
            "motorcycle", "truck", "bird", "chair", "laptop",
        ]
        class_names = {i: name for i, name in enumerate(demo_labels)}
        model_name_short = "DEMO (mock detections)"
        model_path = None
    else:
        model_path = Path(args.model) if args.model else MODEL_PATH
        if model_path is None or not model_path.exists():
            # 自动查找同目录 .pt 文件
            candidates = sorted(
                Path(__file__).resolve().parent.glob("*.pt")
            )
            if candidates:
                model_path = candidates[0]
                print(f"[模型] 自动选择: {model_path}")
            else:
                print("[错误] 未找到 YOLO 模型文件,请用 --model 指定,或使用 --demo 模式")
                sys.exit(1)

        model, class_names = load_model(model_path, args.device)
        model_name_short = model_path.stem[:25]

    # 生成标签映射和颜色映射
    label_mapping = build_label_mapping(class_names)
    color_mapping = build_color_mapping(class_names)

    print(f"[美化] 已映射 {len(label_mapping)} 个中文标签")
    if label_mapping:
        sample_mapped = list(label_mapping.items())[:5]
        print(f"[美化] 示例映射: {sample_mapped}")

    # ── 2. 初始化美化可视化器 ────────────────────────────────
    labels_list = list(class_names.values())
    viz = BeautifyVisualizer(
        labels=labels_list,
        label_mapping=label_mapping,
        color_mapping=color_mapping,
        default_color=(180, 180, 180),
    )
    print("[美化] BeautifyVisualizer 初始化完成")

    # ── 3. 创建帧输入源 ──────────────────────────────────────
    source_path = args.source
    is_camera = source_path in ("0", "1", "2", "/dev/video0", "/dev/video1")

    if is_camera:
        cfg = CameraConfig(
            width=CAMERA_WIDTH,
            height=CAMERA_HEIGHT,
            fps=CAMERA_FPS,
            backend=CAMERA_BACKEND,
        )
        if args.no_thread:
            src = create_frame_source(source_path, camera_config=cfg)
            src_type = "同步"
        else:
            src = create_threaded_source(
                source_path,
                camera_config=cfg,
                warmup_frames=args.warmup,
            )
            src_type = "线程化"
        print(f"[输入] 摄像头 #{source_path} ({src_type})")
        print(f"        目标: {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps ({CAMERA_BACKEND})")
    else:
        if args.no_thread:
            src = create_frame_source(source_path)
            src_type = "同步"
        else:
            src = create_threaded_source(source_path)
            src_type = "线程化"
        print(f"[输入] {source_path} ({src_type})")

    # ── 4. 状态变量 ──────────────────────────────────────────
    use_label_mapping = True         # 默认显示中文
    show_detections = True           # 默认显示检测框
    show_osd = True                  # 默认显示 FPS 面板

    frame_count = 0
    fps_display = 0.0
    fps_timer = time.time()
    fps_update_interval = 0.5
    last_display = 0.0
    infer_ms = 0.0
    num_detections = 0
    resolution = (0, 0)

    screenshot_count = 0
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 5. 主循环 ────────────────────────────────────────────
    print()
    print("=" * 62)
    print("  frame_source + BeautifyVisualizer 联合测试")
    if args.demo:
        print(f"  模式: DEMO (随机模拟检测框)")
    else:
        print(f"  模型: {model_path.name}")
    print(f"  类别: {len(class_names)} 类")
    print(f"  标签: {'中文映射' if use_label_mapping else '英文原版'}")
    print(f"  输入: {'摄像头' if is_camera else source_path}")
    print(f"  模式: {src_type}")
    print(f"  按键: q/ESC=退出  s=截图  m=中/英  d=框开关  f=面板开关")
    print("=" * 62)
    print()

    with src as stream:
        for frame in stream:
            now = time.perf_counter()
            frame_count += 1

            # 首帧打印实际参数
            if frame_count == 1:
                actual_w, actual_h = frame.width, frame.height
                resolution = (actual_w, actual_h)
                print(f"[实际] 分辨率: {actual_w}x{actual_h}")

            # ── 推理 (YOLO / Demo) ────────────────────────────
            infer_t0 = time.perf_counter()
            if args.demo:
                boxes, confs, labels = generate_mock_detections(
                    frame.image, class_names, num_dets=6,
                )
            else:
                boxes, confs, labels = yolo_inference(
                    model, frame.image,
                    conf=args.conf,
                    device=args.device,
                )
            infer_dt = time.perf_counter() - infer_t0
            infer_ms = infer_dt * 1000
            num_detections = len(boxes)

            # ── 构造 Detection 列表 ──────────────────────────
            detections = BeautifyVisualizer.from_yolo_results(
                boxes=boxes,
                confidences=confs,
                labels=labels,
                color_mapping=color_mapping,
            )

            # ── 美化绘制 ─────────────────────────────────────
            if show_detections and detections:
                annotated = viz.draw(
                    frame.image,
                    detections,
                    use_label_mapping=use_label_mapping,
                )
            else:
                annotated = frame.image.copy()

            # ── FPS 计算 ─────────────────────────────────────
            elapsed = now - fps_timer
            if elapsed >= fps_update_interval:
                fps_display = frame_count / elapsed
                frame_count = 0
                fps_timer = now

            # ── OSD 叠加 ─────────────────────────────────────
            display = annotated
            if show_osd:
                display = draw_osd(
                    display.copy(),
                    fps=fps_display,
                    frame_idx=frame.info.frame_index,
                    use_mapping=use_label_mapping,
                    show_detections=show_detections,
                    resolution=resolution,
                    infer_ms=infer_ms,
                    num_dets=num_detections,
                    model_name=model_name_short,
                )

            # ── 显示 (限 30fps) ──────────────────────────────
            if now - last_display >= DISPLAY_INTERVAL:
                last_display = now
                cv2.imshow(DISPLAY_WINDOW, display)
                key = cv2.waitKey(1) & 0xFF
            else:
                key = cv2.pollKey() & 0xFF if hasattr(cv2, 'pollKey') else 0xFF

            # ── 按键处理 ─────────────────────────────────────
            if key == 27 or key == ord("q"):  # ESC / q → 退出
                print("\n[用户] 退出")
                break
            elif key == ord("s"):              # s → 截图
                screenshot_count += 1
                filename = SCREENSHOT_DIR / (
                    f"beautify_{screenshot_count:04d}_"
                    f"frame{frame.info.frame_index:06d}.jpg"
                )
                cv2.imwrite(str(filename), display)
                print(f"  [截图] 已保存: {filename}")
            elif key == ord("m"):              # m → 切换中/英文
                use_label_mapping = not use_label_mapping
                print(f"  [切换] 标签语言: {'中文' if use_label_mapping else '英文'}")
            elif key == ord("d"):              # d → 切换检测框
                show_detections = not show_detections
                print(f"  [切换] 检测框: {'显示' if show_detections else '隐藏'}")
            elif key == ord("f"):              # f → 切换 FPS 面板
                show_osd = not show_osd
                print(f"  [切换] 信息面板: {'显示' if show_osd else '隐藏'}")

    # ── 6. 清理 ──────────────────────────────────────────────
    cv2.destroyAllWindows()
    print(f"\n[Done] 共处理约 {frame.info.frame_index + 1} 帧")
    if screenshot_count:
        print(f"       截图 {screenshot_count} 张 → {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
