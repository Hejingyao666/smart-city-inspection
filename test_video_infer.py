#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""视频推理测试脚本"""
from pathlib import Path
from odp_platform.inference import infer_yolo

def test_video_inference(video_path: str, model_path: str = "yolo11n.pt"):
    """
    使用视频文件测试推理
    
    Args:
        video_path: 视频文件路径
        model_path: 模型文件路径
    """
    video = Path(video_path)
    if not video.exists():
        print(f"错误: 视频文件不存在 - {video_path}")
        return
    
    print(f"开始视频推理测试")
    print(f"视频文件: {video_path}")
    print(f"模型文件: {model_path}")
    print("=" * 60)
    
    # 使用配置覆盖的方式运行推理
    result = infer_yolo(
        yaml_path="infer.yaml",
        cli_args={
            "source": video_path,
            "model": model_path,
            "show": True,      # 显示画面
            "save": True,      # 保存结果
            "conf": 0.25,      # 置信度阈值
            "device": "cpu",   # 使用 CPU
            "batch": 8,        # 批处理大小
        }
    )
    
    print("=" * 60)
    if result.success:
        print(f"推理成功!")
        print(f"输出目录: {result.output_dir}")
        print(f"处理帧数: {result.stats.get('frames', 0)}")
        print(f"检测总数: {result.stats.get('detections', 0)}")
        print(f"平均帧率: {result.stats.get('avg_fps', 0):.2f} FPS")
        if result.log_path:
            print(f"日志文件: {result.log_path}")
    else:
        print(f"推理失败: {result.error}")

if __name__ == "__main__":
    # 提示用户提供视频文件路径
    print("请确保视频文件存在于项目目录中")
    print("支持的视频格式: mp4, avi, mov, mkv, flv, wmv, webm")
    print()
    
    # 检查是否有示例视频
    import glob
    videos = glob.glob("*.mp4") + glob.glob("*.avi") + glob.glob("*.mov")
    
    if videos:
        print("找到以下视频文件:")
        for i, v in enumerate(videos, 1):
            print(f"  {i}. {v}")
        print()
        
        # 使用第一个找到的视频进行测试
        print(f"使用视频: {videos[0]}")
        test_video_inference(videos[0])
    else:
        print("未找到视频文件，请将视频文件放到项目根目录后再运行")
        print("或修改脚本中的 video_path 参数")