"""测试 pascal_voc converter。"""
import pytest
from pathlib import Path

from odp_platform.data_pipeline.registry import get_converter, ConvertOptions
from odp_platform.common.constants import AnnotationFormat


class TestPascalVocConverter:

    def test_converts_xml_to_txt(self, voc_dir: Path, output_dir: Path):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        options = ConvertOptions()
        entry.func(voc_dir, output_dir, options)

        txt_files = sorted(output_dir.glob("*.txt"))
        assert len(txt_files) == 3
        assert txt_files[0].stem == "img_0000"

    def test_discovers_classes(self, voc_dir: Path, output_dir: Path):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        options = ConvertOptions()
        classes = entry.func(voc_dir, output_dir, options)

        assert "cat" in classes
        assert "dog" in classes
        assert len(classes) == 2

    def test_yolo_format_output(self, voc_dir: Path, output_dir: Path):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        options = ConvertOptions()
        entry.func(voc_dir, output_dir, options)

        txt = (output_dir / "img_0000.txt").read_text(encoding="utf-8")
        lines = txt.strip().split("\n")
        assert len(lines) == 2

        parts = lines[0].split()
        assert len(parts) == 5
        cls_id = int(parts[0])
        assert cls_id >= 0
        for val in parts[1:]:
            assert 0.0 <= float(val) <= 1.0

    def test_empty_dir_raises(self, tmp_path: Path, output_dir: Path):
        empty = tmp_path / "empty"
        empty.mkdir()

        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        options = ConvertOptions()

        with pytest.raises(FileNotFoundError):
            entry.func(empty, output_dir, options)

    def test_explicit_classes_filter(self, voc_dir: Path, output_dir: Path):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        options = ConvertOptions(classes=["cat"])
        classes = entry.func(voc_dir, output_dir, options)

        assert classes == ["cat"]
        txt = (output_dir / "img_0000.txt").read_text(encoding="utf-8")
        for line in txt.strip().split("\n"):
            assert line.split()[0] == "0"
