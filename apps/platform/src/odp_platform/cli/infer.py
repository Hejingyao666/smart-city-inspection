from __future__ import annotations

import argparse
import sys

from odp_platform.inference.service import InferService


def build_parser():
    parser = argparse.ArgumentParser(
        prog="odp-infer",
        description="图片推理"
    )

    parser.add_argument(
        "--weights",
        required=True,
        help="best.pt 路径"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="图片路径"
    )

    parser.add_argument(
        "--imgsz",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--device",
        default="0",
    )

    return parser


def main():
    args = build_parser().parse_args()

    service = InferService(
        weights=args.weights
    )

    service.predict_image(
        source=args.source,
        imgsz=args.imgsz,
        device=args.device,
    )

    print("推理完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())