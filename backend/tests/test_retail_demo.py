"""I0 acceptance: local CLI, metric parity and failed-input behavior."""

import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree as ET

import ezdxf
import pytest

from src.retail.layout import RetailLayout
from src.retail.preview import export_svg

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/retail-demo.json"
NS = {"s": "http://www.w3.org/2000/svg"}


def run_demo(source, output):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "backend"))
    env.pop("HF_TOKEN", None)
    env.pop("HF_RETAIL_SPACE_ID", None)
    return subprocess.run(
        [sys.executable, "-m", "src.retail.demo", str(source), str(output)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_cli_exports_metric_equivalent_geometry(tmp_path):
    output = tmp_path / "generated"
    result = run_demo(EXAMPLE, output)
    assert result.returncode == 0, result.stderr
    assert set(p.name for p in output.iterdir()) == {
        "retail-layout.dxf",
        "retail-layout.svg",
        "validation.json",
    }
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    doc = ezdxf.read(StringIO((output / "retail-layout.dxf").read_text()))
    assert doc.units == 6
    assert not doc.audit().errors
    svg = ET.parse(output / "retail-layout.svg")
    assert float(svg.getroot().attrib["height"]) == 960
    group = svg.find("s:g[@id='metric-geometry']", NS)
    assert group.attrib["transform"] == "translate(0 10) scale(1 -1)"
    rectangles = group.findall("s:rect", NS)
    items = [dict(x=0, y=0, width=data["width"], depth=data["depth"])]
    items += data["clear_zones"] + data["fixtures"]
    polygons = list(doc.modelspace().query("LWPOLYLINE"))
    assert len(rectangles) == len(polygons) == len(items)
    actual_dxf = set()
    for poly in polygons:
        points = list(poly.get_points("xy"))
        xs, ys = zip(*points)
        actual_dxf.add((min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))
    for rect, item in zip(rectangles, items):
        geometry = tuple(float(rect.attrib[k]) for k in ("x", "y", "width", "height"))
        expected = tuple(item[k] for k in ("x", "y", "width", "depth"))
        assert geometry == expected
        assert geometry in actual_dxf
    report = json.loads((output / "validation.json").read_text())
    assert report["scope"] == "declared_geometry_only"
    assert "connection_usable_width" in report["pending"]
    assert "commercial_review" in report["pending"]
    assert report["lighting_intent"]["status"] == "declared_intent"


@pytest.mark.parametrize("case", ["blocked", "schema", "json", "missing"])
def test_cli_failure_produces_no_exports(tmp_path, case):
    source = tmp_path / "input.json"
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    if case == "blocked":
        data["fixtures"][0]["x"] = 10
    elif case == "schema":
        data["width"] = -1
    if case != "missing":
        source.write_text("{broken" if case == "json" else json.dumps(data))
    output = tmp_path / "generated"
    result = run_demo(source, output)
    assert result.returncode != 0
    assert "Export failed:" in result.stderr
    assert not output.exists()


def test_cli_preserves_existing_outputs(tmp_path):
    output = tmp_path / "generated"
    output.mkdir()
    marker = output / "retail-layout.svg"
    marker.write_text("existing work")
    result = run_demo(EXAMPLE, output)
    assert result.returncode != 0
    assert marker.read_text() == "existing work"
    assert not (output / "validation.json").exists()


def test_svg_escapes_user_labels():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["name"] = '<script>alert("x")</script> & loja'
    data["fixtures"][0]["category"] = "Frutas & legumes <frescos>"
    svg = ET.fromstring(export_svg(RetailLayout(**data)))
    assert svg.find("s:title", NS).text == data["name"]
    assert not svg.findall(".//s:script", NS)
    assert any(
        e.text == data["fixtures"][0]["category"] for e in svg.findall(".//s:text", NS)
    )
