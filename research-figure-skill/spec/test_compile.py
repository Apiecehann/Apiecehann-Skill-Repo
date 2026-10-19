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
