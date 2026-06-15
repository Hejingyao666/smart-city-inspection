#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""DIOR模型测试脚本"""
from pathlib import Path
from ultralytics import YOLO

def test_dior_model(model_path: str, test_image_path: str = None):
    """
    测试DIOR训练模型
    
    Args:
        model_path: 模型文件路径
        test_image_path: 测试图片路径（可选，默认使用摄像头）
    """
    model_file = Path(model_path)
    if not model_file.exists():
        print(f"错误: 模型文件不存在 - {model_path}")
        return
    
    print(f"加载DIOR训练模型: {model_path}")
    print("=" * 60)
    
    try:
        # 加载模型
        model = YOLO(model_path)
        
        # 打印模型信息
        print("模型信息:")
        print(f"  模型类型: {model.__class__.__name__}")
        print(f"  类别数量: {len(model.names)}")
        print(f"  类别列表: {list(model.names.values())}")
        print()
        
        # 测试方式选择
        if test_image_path and Path(test_image_path).exists():
            print(f"使用图片测试: {test_image_path}")
            results = model.predict(
                source=test_image_path,
                conf=0.25,
                show=True,
                save=True,
                device="cpu"
            )
        else:
            print("使用摄像头测试 (按 'q' 退出)")
            print("注意: DIOR模型是为遥感影像训练的，可能对普通摄像头画面检测效果有限")
            results = model.predict(
                source=0,
                conf=0.25,
                show=True,
                device="cpu"
            )
        
        # 打印检测结果
        print("\n检测结果:")
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = model.names.get(cls, f"类别{cls}")
                    print(f"  [{label}] 置信度: {conf:.2f}")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # DIOR模型路径
    dior_model_path = r"d:\od\ODPlatform\runs\detect_train\train-13\weights\best.pt"
    
    print("DIOR模型测试工具")
    print("=" * 60)
    print("DIOR数据集包含以下类别:")
    print("  airplane, airport, baseball diamond, basketball court, beach")
    print("  bridge, church, commercial area, forest, freeway, golf course")
    print("  harbor, industrial area, lake, mountain, parking lot, railway")
    print("  river, ship, stadium, storage tank, wetland, 等45个类别")
    print("=" * 60)
    
    # 测试模型
    test_dior_model(dior_model_path)
