"""Semantic IR contracts and replay through the sole rendering backend."""
import copy
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from compile import compile_ir, load_ir, backend

SPEC = Path(__file__).resolve().parent


@pytest.fixture
def source(tmp_path):
    ir = {
        "claim": "Compare two mock methods.", "chart": "grouped-bar", "data": "source.csv",
        "encoding": {"x": "task", "y": "score", "series": "method"},
        "size": {"preset": "single"},
        "theme": {"style": "soft-outline", "palette": "tol-bright", "font": "sans"},
        "labels": {"values": False, "legend": "top"},
        "output": {"formats": ["png", "pdf", "svg"], "dpi": 100, "svg_text": True},
        "series_order": ["base", "ours"], "axis": {"y_format": ".0%"},
    }
    (tmp_path / "source.csv").write_text("task,method,score\nA,ours,0.8\nA,base,0.5\nB,base,0.6\nB,ours,0.9\n", encoding="utf8")
    path = tmp_path / "figure.ir.json"
    path.write_text(json.dumps(ir), encoding="utf8")
    return path, ir


def save(source):
    path, ir = source
    path.write_text(json.dumps(ir), encoding="utf8")
    return path


def test_valid_ir_and_portable_renderer_input(source, tmp_path):
    config, decisions = compile_ir(source[0], tmp_path / "build")
    assert (tmp_path / "build/config.json").exists()
    assert (tmp_path / "build/decisions.json").exists()
    rows = backend.load_data(tmp_path / "build" / config["data"])
    assert [r["series"] for r in rows] == ["base", "ours", "base", "ours"]
    assert rows[0]["id"] == "row-0002"
    assert config["figure"]["size_pt"] == [237.6, 169.7]
    assert config["panel_defaults"]["limits"] == "auto"
    assert decisions["axes"]["main"]["limits"][1] >= .9


@pytest.mark.parametrize("mutation, message", [
    (lambda ir: ir.update(unknown=True), "unknown field"),
    (lambda ir: ir["theme"].update(unknown=True), "unknown field"),
    (lambda ir: ir.update(chart="scatter"), "grouped-bar"),
    (lambda ir: ir["labels"].update(values=1), "boolean"),
    (lambda ir: ir.update(series_order=["ours", "ours"]), "unique"),
    (lambda ir: ir.update(series_order=["ours"]), "every plotted series"),
    (lambda ir: ir["encoding"].update(y="absent"), "missing columns"),
])
def test_invalid_ir_fails_before_writes(source, tmp_path, mutation, message):
    mutation(source[1])
    with pytest.raises(ValueError, match=message):
        compile_ir(save(source), tmp_path / "build")
    assert not (tmp_path / "build").exists()


def test_percentage_range_is_validated(source, tmp_path):
    (tmp_path / "source.csv").write_text("task,method,score\nA,base,80\nA,ours,90\n")
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        compile_ir(source[0], tmp_path / "build")


def test_dry_run_cli_never_renders(source, tmp_path):
    result = subprocess.run([sys.executable, str(SPEC / "compile.py"), "--ir", str(source[0]),
                             "--output", str(tmp_path / "build"), "--dry-run"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "size single" in result.stdout
    assert sorted(p.name for p in (tmp_path / "build").iterdir()) == ["config.json", "data.csv", "decisions.json"]


def test_compile_render_and_replay(source, tmp_path):
    config, _ = compile_ir(source[0], tmp_path / "build", render=True)
    for ext in ("png", "pdf", "svg"):
        assert (tmp_path / f"build/figure.{ext}").stat().st_size > 1000
    assert "<text" in (tmp_path / "build/figure.svg").read_text()
    subprocess.run([sys.executable, str(Path(backend.__file__)), "--config",
                    str(tmp_path / "build/config.json"), "--output", str(tmp_path / "replay")],
                   cwd=tmp_path, check=True, capture_output=True)
    assert (tmp_path / "replay.png").read_bytes() == (tmp_path / "build/figure.png").read_bytes()

TEMPLATES = SPEC.parent / "examples/templates"


def test_focus_gray_keeps_alpha_and_hatch(source, tmp_path):
    ir = source[1]
    ir["emphasis"] = [{"card": "focus-gray", "series": "ours"}]
    ir["theme"]["series_styles"] = {"base": {"fill_alpha": .4, "hatch": "/"}}
    config, _ = compile_ir(save(source), tmp_path / "build")
    assert config["palette"]["ours"]["fill"] == "#9979CB"
    assert config["palette"]["base"]["fill"] == "#A3ACB9"
    assert config["palette"]["base"]["edge"] == "#57606C"
    assert config["palette"]["base"]["fill_alpha"] == .4
    assert config["palette"]["base"]["hatch"] == "/"


def test_delta_resolves_row_ids(source, tmp_path):
    source[1]["annotations"] = [{"card": "delta", "group": "B", "from": "base", "to": "ours", "label_scale": 100}]
    config, decisions = compile_ir(save(source), tmp_path / "build")
    gain = config["gains"][0]
    assert (gain["from"], gain["to"]) == ("row-0003", "row-0004")
    assert gain["label_scale"] == 100
    assert "(+30.0)" in "\n".join(decisions["log"])


@pytest.mark.parametrize("card_request, message", [
    ({"card": "missing", "group": "A", "from": "base", "to": "ours"}, "Unknown annotation card"),
    ({"card": "delta", "from": "base", "to": "ours"}, "specify matching group and panel"),
    ({"card": "delta", "group": "A", "from": "ours", "to": "ours"}, "distinct"),
])
def test_invalid_annotation(source, tmp_path, card_request, message):
    source[1]["annotations"] = [card_request]
    with pytest.raises(ValueError, match=message):
        compile_ir(save(source), tmp_path / "build")


def test_unknown_emphasis_card(source, tmp_path):
    source[1]["emphasis"] = [{"card": "unknown", "series": "ours"}]
    with pytest.raises(ValueError, match="Unknown emphasis card"):
        compile_ir(save(source), tmp_path / "build")


def test_multiple_focus_series_rejected(source, tmp_path):
    source[1]["emphasis"] = [{"card": "focus-gray", "series": s} for s in ("base", "ours")]
    with pytest.raises(ValueError, match="exactly one"):
        compile_ir(save(source), tmp_path / "build")


def test_capacity_config_and_invalid_capacity(source, tmp_path):
    source[1]["encoding"]["capacity"] = "total"
    (tmp_path / "source.csv").write_text("task,method,score,total\nA,base,0.5,1\nA,ours,0.8,1\n")
    config, _ = compile_ir(save(source), tmp_path / "build")
    assert config["panel_defaults"]["capacity"]["field"] == "capacity"
    (tmp_path / "source.csv").write_text("task,method,score,total\nA,base,0.5,0.4\nA,ours,0.8,1\n")
    with pytest.raises(ValueError, match="capacity >= value"):
        compile_ir(source[0], tmp_path / "invalid")


@pytest.mark.parametrize("name", sorted(p.name for p in TEMPLATES.iterdir()))
def test_all_recipes_compile(name, tmp_path):
    config, _ = compile_ir(TEMPLATES / name / "figure.ir.json", tmp_path / name)
    assert config["figure"]["formats"] == ["png", "pdf", "svg"]
    assert "MOCK / layout test" in (TEMPLATES / name / "README.md").read_text()
