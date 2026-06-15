#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""DIOR模型简单测试脚本"""
from pathlib import Path
from ultralytics import YOLO

def test_dior_model_simple(model_path: str):
    """
    简单测试DIOR训练模型 - 仅加载模型并打印信息
    
    Args:
        model_path: 模型文件路径
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
        print(f"  类别列表:")
        for idx, name in sorted(model.names.items()):
            print(f"    {idx}: {name}")
        
        # 打印模型配置
        print("\n模型配置:")
        if hasattr(model, 'model'):
            print(f"  输入尺寸: {model.model.args.get('imgsz', '未知')}")
            print(f"  批大小: {model.model.args.get('batch', '未知')}")
        
        print("\n" + "=" * 60)
        print("模型加载成功!")
        
        # 测试使用第一张测试图片
        test_image = r"d:\od\ODPlatform\data\test\images\plantdoc_002533.jpg"
        if Path(test_image).exists():
            print(f"\n使用测试图片: {test_image}")
            print("正在推理...")
            results = model.predict(
                source=test_image,
                conf=0.25,
                show=False,
                save=True,
                device="cpu"
            )
            
            # 打印检测结果
            print("\n检测结果:")
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = model.names.get(cls, f"类别{cls}")
                        print(f"  [{label}] 置信度: {conf:.2f}")
                else:
                    print("  未检测到目标")
            
            # 输出保存路径
            if results[0].save_dir:
                print(f"\n结果已保存到: {results[0].save_dir}")
        
        else:
            print(f"\n警告: 测试图片不存在: {test_image}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # DIOR模型路径
    dior_model_path = r"d:\od\ODPlatform\runs\detect_train\train-13\weights\best.pt"
    test_dior_model_simple(dior_model_path)
