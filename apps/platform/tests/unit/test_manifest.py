"""测试 SplitManifest 数据结构。"""
from pathlib import Path

from odp_platform.data_pipeline.split.manifest import SplitManifest


class TestSplitManifest:

    def test_empty_manifest(self):
        m = SplitManifest()
        assert m.train == []
        assert m.val == []
        assert m.test == []

    def test_summary_counts(self):
        m = SplitManifest()
        m.train = [(Path("a.jpg"), Path("a.txt")), (Path("b.jpg"), Path("b.txt"))]
        m.val = [(Path("c.jpg"), Path("c.txt"))]
        m.test = []

        s = m.summary()
        assert s["train"] == 2
        assert s["val"] == 1
        assert s["test"] == 0
        assert s["total"] == 3

    def test_default_strategy(self):
        m = SplitManifest()
        assert m.strategy == "random"

    def test_custom_fields(self):
        m = SplitManifest(
            train_rate=0.7,
            val_rate=0.2,
            test_rate=0.1,
            random_state=123,
            strategy="stratified",
        )
        assert m.train_rate == 0.7
        assert m.random_state == 123
        assert m.strategy == "stratified"
