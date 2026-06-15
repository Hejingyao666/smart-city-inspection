"""共享 fixtures。"""
import pytest
from pathlib import Path

# ─── VOC 样本 XML ───────────────────────────────────────────
SAMPLE_VOC_XML = """\
<annotation>
  <size>
    <width>640</width>
    <height>480</height>
    <depth>3</depth>
  </size>
  <object>
    <name>cat</name>
    <bndbox>
      <xmin>100</xmin>
      <ymin>50</ymin>
      <xmax>300</xmax>
      <ymax>250</ymax>
    </bndbox>
  </object>
  <object>
    <name>dog</name>
    <bndbox>
      <xmin>320</xmin>
      <ymin>100</ymin>
      <xmax>600</xmax>
      <ymax>400</ymax>
    </bndbox>
  </object>
</annotation>
"""


@pytest.fixture
def voc_dir(tmp_path: Path) -> Path:
    """创建一个含有 3 个样本 XML 的临时 VOC 目录。"""
    xml_dir = tmp_path / "annotations"
    xml_dir.mkdir()
    for i in range(3):
        (xml_dir / f"img_{i:04d}.xml").write_text(SAMPLE_VOC_XML, encoding="utf-8")
    return xml_dir


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """空的输出目录。"""
    out = tmp_path / "labels"
    out.mkdir()
    return out
