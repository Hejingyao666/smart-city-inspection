#!/usr/bin/env python
# -*- coding:utf-8 -*-
# scripts/make_disaster_data.py
# 创建灾难现场数据，用于测试 odp-reset

import os
from pathlib import Path

def create_disaster_data():
    """创建测试用的灾难现场数据"""
    root = Path.cwd()
    
    print("=" * 60)
    print("🎬 准备灾难现场...")
    print("=" * 60)
    
    # 1. 珍贵标注数据（要保护！）
    precious_dir = root / "data" / "raw" / "precious_dataset"
    precious_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(400):
        anno_file = precious_dir / f"annotation_{i:04d}.json"
        anno_file.write_text(f'{{"id": {i}, "precious": true}}\n')
    
    print(f"✓ 创建珍贵标注数据: {precious_dir.relative_to(root)} (400 文件)")
    
    # 2. 2GB 稀疏文件（模型权重）
    exp_dir = root / "runs" / "exp_2026_05_10"
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = exp_dir / "best.pt"
    with open(model_file, 'wb') as f:
        f.seek(2 * 1024 * 1024 * 1024 - 1)  # 2GB - 1 byte
        f.write(b'\0')
    
    print(f"✓ 创建稀疏模型文件: {model_file.relative_to(root)} (2GB)")
    
    # 3. 日志文件
    logs_dir = root / "apps" / "platform" / "logging" / "training" / "2026-05-10"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(50):
        log_file = logs_dir / f"run_{i:03d}.log"
        log_content = f"""2026-06-09 10:00:{i:02d} [INFO] Training started
2026-06-09 10:00:05 [DEBUG] Loading model...
2026-06-09 10:00:10 [INFO] Epoch 1/100
2026-06-09 10:01:00 [INFO] Loss: 0.5432
"""
        log_file.write_text(log_content)
    
    print(f"✓ 创建日志文件: {logs_dir.relative_to(root)} (50 文件)")
    
    # 4. 5000 个小数据文件
    train_dir = root / "data" / "train" / "images"
    train_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(5000):
        img_file = train_dir / f"image_{i:05d}.jpg"
        img_file.write_text(f"fake image data {i}")
        
        if (i + 1) % 1000 == 0:
            print(f"  已创建 {i + 1}/5000 小文件...")
    
    print(f"✓ 创建小数据文件: {train_dir.relative_to(root)} (5000 文件)")
    
    print("=" * 60)
    print("🎬 灾难现场准备完成！")
    print("文件统计:")
    print("  - 珍贵标注数据: data/raw/precious_dataset/ (400 文件)")
    print("  - 稀疏模型: runs/exp_2026_05_10/best.pt (2GB)")
    print("  - 日志文件: apps/platform/logging/training/ (50 文件)")
    print("  - 小数据文件: data/train/images/ (5000 文件)")
    print("=" * 60)

if __name__ == "__main__":
    create_disaster_data()