"""Semantic IR contracts and replay through the sole rendering backend."""
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
    (lambda ir: ir.update(chart="pie"), "choose from"),
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


@pytest.mark.parametrize("name", sorted(p.name for p in TEMPLATES.iterdir()))
def test_every_recipe_renders_without_warnings_and_matches_decisions(name, tmp_path):
    import warnings
    path = tmp_path / name
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config, decisions = compile_ir(TEMPLATES / name / "figure.ir.json", path, render=True)
        if decisions["chart"] != "grouped-bar":
            for ext in ("png", "pdf", "svg"):
                assert (path / f"figure.{ext}").stat().st_size > 1000
            assert "<text" in (path / "figure.svg").read_text()
            return
        rows = backend.load_data(path / "data.csv")
        fig, artists = backend.build_figure(config, rows)
    try:
        assert len(artists) == len(rows)
        for panel, ax in zip(config["panels"], fig.axes):
            limits = ax.get_xlim() if config["panel_defaults"]["orientation"] == "horizontal" else ax.get_ylim()
            assert list(limits) == decisions["axes"][panel["id"]]["limits"]
        if name == "capacity-88-of-96":
            assert next(iter(artists.values()))["capacity_label"].get_text() == "88 / 96 (92%)"
        if name == "print-bw":
            assert all(a["bar"].get_hatch() for a in artists.values())
        for ext in ("png", "pdf", "svg"):
            assert (path / f"figure.{ext}").stat().st_size > 1000
        svg = (path / "figure.svg").read_text()
        assert "<text" in svg and "<image" not in svg
        assert b"/Subtype /Image" not in (path / "figure.pdf").read_bytes()
    finally:
        backend.plt.close(fig)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "bad"])
def test_nonfinite_or_nonnumeric_data_rejected(source, tmp_path, value):
    (tmp_path / "source.csv").write_text(f"task,method,score\nA,base,{value}\n")
    with pytest.raises(ValueError, match="number|finite"):
        compile_ir(source[0], tmp_path / "build")


@pytest.mark.parametrize("mutation, message", [
    (lambda ir: ir["theme"].update(type_scale=True), "number"),
    (lambda ir: ir["axis"].update(y_max=.6), "clip"),
    (lambda ir: ir["axis"].update(y_format="wrong-format"), "Invalid numeric format"),
    (lambda ir: ir["output"].update(formats=["png", "png"]), "unique"),
    (lambda ir: ir["emphasis"][0].update(series="absent"), "absent from CSV"),
    (lambda ir: ir["emphasis"][0].update(accent="invalid-color"), "invalid accent"),
])
def test_additional_semantic_failures(source, tmp_path, mutation, message):
    source[1]["emphasis"] = [{"card": "focus-gray", "series": "ours"}]
    mutation(source[1])
    with pytest.raises(ValueError, match=message):
        compile_ir(save(source), tmp_path / "build")


def test_delta_disambiguates_panel(source, tmp_path):
    source[1]["encoding"]["panel"] = "env"
    (tmp_path / "source.csv").write_text(
        "id,env,task,method,score\na,p,A,base,.3\nb,p,A,ours,.5\nc,q,A,base,.4\nd,q,A,ours,.8\n")
    source[1]["annotations"] = [{"card": "delta", "group": "A", "from": "base", "to": "ours"}]
    with pytest.raises(ValueError, match="specify matching group and panel"):
        compile_ir(save(source), tmp_path / "build")
    source[1]["annotations"][0]["panel"] = "q"
    config, _ = compile_ir(save(source), tmp_path / "build")
    assert config["gains"][0]["from"] == "c"
    assert config["gains"][0]["to"] == "d"


def test_capacity_interval_is_rejected_before_output(source, tmp_path):
    source[1]["encoding"]["capacity"] = "total"
    (tmp_path / "source.csv").write_text("task,method,score,total,low,high\nA,base,.5,1,.4,.6\nA,ours,.8,1,.7,.9\n")
    with pytest.raises(ValueError, match="interval.*capacity"):
        compile_ir(save(source), tmp_path / "build")
    assert not (tmp_path / "build").exists()


def test_invalid_input_cli_has_actionable_error_and_no_traceback(source, tmp_path):
    source[1]["encoding"]["y"] = "absent"
    result = subprocess.run([sys.executable, str(SPEC / "compile.py"), "--ir", str(save(source)),
                             "--output", str(tmp_path / "build"), "--dry-run"],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "missing columns" in result.stderr
    assert "Traceback" not in result.stderr


def test_catalog_indexes_generated_artifacts(tmp_path):
    from PIL import Image
    output = tmp_path / "catalog"
    subprocess.run([sys.executable, str(SPEC / "catalog.py"), "--output", str(output)],
                   check=True, capture_output=True, text=True)
    index = json.loads((output / "index.json").read_text())
    assert len(index["entries"]) == 43
    assert len({e["recipe"] for e in index["entries"]}) == 43
    for entry in index["entries"]:
        assert entry["tags"]
        assert entry["decisions"]["size"] in ("single", "medium", "double")
        for relative in entry["files"].values():
            assert not Path(relative).is_absolute()
            assert (output / relative).is_file()
    with Image.open(output / "contact-sheet.png") as sheet:
        assert sheet.width > 1000 and sheet.height > 1000
        assert sheet.convert("L").getextrema()[0] < 100


def test_eval_templates_pass_and_produced_ir_is_checked(tmp_path):
    check = SPEC / "evals/check.py"
    cases = SPEC / "evals/cases.jsonl"
    result = subprocess.run([sys.executable, str(check), "--cases", str(cases), "--check-templates"],
                            check=True, capture_output=True, text=True)
    assert "PASS 47" in result.stdout
    result = subprocess.run([sys.executable, str(check), "--cases", str(cases), "--case", "case-01",
                             "--ir", str(TEMPLATES / "ours-vs-baselines/figure.ir.json")],
                            check=True, capture_output=True, text=True)
    assert "PASS 1" in result.stdout
    ir = json.loads((TEMPLATES / "ours-vs-baselines/figure.ir.json").read_text())
    ir["data"] = str(TEMPLATES / "ours-vs-baselines/data.csv")
    ir["size"]["preset"] = "double"
    bad = tmp_path / "wrong.ir.json"
    bad.write_text(json.dumps(ir))
    result = subprocess.run([sys.executable, str(check), "--cases", str(cases), "--case", "case-01",
                             "--ir", str(bad)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "IR.size" in result.stderr


def test_auto_axis_keeps_tight_headroom():
    limits, ticks = backend.auto_axis([{"value": .85}], 0)
    assert limits == [0.0, .9]
    assert ticks[-1] == .9


def test_capacity_single_group_is_narrow(tmp_path):
    config, decisions = compile_ir(TEMPLATES / "capacity-88-of-96/figure.ir.json", tmp_path / "cap")
    assert config["panel_defaults"]["bar_width"] == .35
    assert config["panel_defaults"]["category_margin"] == .55
    assert any("bar width 0.35" in line for line in decisions["log"])


def test_horizontal_single_series_is_tight_and_gridless(tmp_path):
    config, decisions = compile_ir(TEMPLATES / "horizontal-percent/figure.ir.json", tmp_path / "horiz")
    assert config["panel_defaults"]["group_gap"] == .06
    assert config["panel_defaults"]["grid"]["kind"] == "none"
    assert any("group gap 0.06" in line for line in decisions["log"])


def test_axes_catalog_declares_when_and_avoid_for_every_option():
    axes = json.loads((SPEC.parent / "library/axes.json").read_text(encoding="utf8"))["axes"]
    assert {"baseline_strategy", "accent_hue", "paired_palette", "categorical_palette",
            "grid", "style", "type", "annotation", "layout", "size"} <= set(axes)
    for name, axis in axes.items():
        assert axis["options"], name
        for option in axis["options"]:
            assert option["id"] and option["label"], (name, option)
            assert option["when"] and option["avoid"], (name, option)
            assert option.get("status") in ("implemented", "planned"), (name, option)


def test_increment_ir_normalizes_custom_column_and_uses_existing_backend(source, tmp_path):
    source[1]["encoding"]["base"] = "previous"
    (tmp_path / "source.csv").write_text("task,method,previous,score\nA,base,.3,.5\nA,ours,.5,.8\n")
    config, decisions = compile_ir(save(source), tmp_path / "build", render=True)
    assert config["panel_defaults"]["increment"]["field"] == "base"
    assert config["panel_defaults"]["increment"]["gap_pt"] == 1.5
    assert decisions["encoding"] == ["increment"]
    assert backend.load_data(tmp_path / "build/data.csv")[0]["base"] == .3
    assert (tmp_path / "build/figure.svg").is_file()


def test_palette_library_has_120_unique_four_color_cards():
    library = json.loads((SPEC.parent / "library/palettes-120.json").read_text(encoding="utf8"))
    assert library["count"] == 120
    assert len(library["palettes"]) == 120
    assert len({tuple(p["colors"]) for p in library["palettes"]}) == 120
    assert all(len(p["colors"]) == 4 for p in library["palettes"])


def test_chart_and_overlay_registries_are_consistent():
    charts = json.loads((SPEC.parent / "library/charts.json").read_text(encoding="utf8"))["charts"]
    overlays = json.loads((SPEC.parent / "library/overlays.json").read_text(encoding="utf8"))["overlays"]
    chart_ids = [c["id"] for c in charts]
    overlay_ids = [o["id"] for o in overlays]
    assert len(chart_ids) == len(set(chart_ids))
    assert len(overlay_ids) == len(set(overlay_ids))
    for chart in charts:
        assert chart["family"] and chart["requires"]
        assert all(o in overlay_ids or o == "*" for o in chart["supports"])
    for overlay in overlays:
        assert overlay["layer"] in ("stat", "reference", "annotation")
        assert all(c in chart_ids or c == "*" for c in overlay["supports"])
