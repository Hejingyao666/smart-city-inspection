"""测试注册表机制。"""
import pytest
from odp_platform.common.constants import AnnotationFormat, Task
from odp_platform.data_pipeline.registry import (
    get_converter,
    list_capabilities,
    ConverterEntry,
)


class TestRegistry:
    """注册表核心功能。"""

    def test_pascal_voc_registered(self):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        assert isinstance(entry, ConverterEntry)
        assert callable(entry.func)

    def test_coco_registered(self):
        entry = get_converter(AnnotationFormat.COCO)
        assert isinstance(entry, ConverterEntry)

    def test_yolo_registered(self):
        entry = get_converter(AnnotationFormat.YOLO)
        assert isinstance(entry, ConverterEntry)

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError):
            get_converter("unknown_format_xyz")

    def test_list_capabilities_returns_all(self):
        caps = list_capabilities()
        assert AnnotationFormat.PASCAL_VOC in caps
        assert AnnotationFormat.COCO in caps
        assert AnnotationFormat.YOLO in caps

    def test_supported_tasks_detect(self):
        entry = get_converter(AnnotationFormat.PASCAL_VOC)
        assert Task.DETECT in entry.supported_tasks
