"""Behaviour checks: changed data, different groups, intervals and style overrides."""
import csv
import json
import subprocess
import sys
import warnings
from pathlib import Path
import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.transforms import Affine2D
from render import (DEFAULTS, build_figure, load_data, merge, apply_override,
                    apply_override_file, panel_rectangles, render)

EXAMPLES=Path(__file__).resolve().parents[1]/'examples'


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')

def case(name='cue-comparison'):
    p=EXAMPLES/name
    config=json.loads((p/'config.json').read_text(encoding='utf8'))
    for icon in config.get('icons',[]):
        if 'image' in icon:icon['image']=str(p/icon['image'])
    return config,load_data(p/'data.csv')

def test_replacing_data_moves_bar_interval_and_label():
    config,rows=case();rows[0].update(value=.10,low=.07,high=.13)
    fig,a=build_figure(config,rows)
    assert a['math-0']['bar'].get_height()==.10
    np.testing.assert_allclose(a['math-0']['error'].lines[2][0].get_segments()[0][:,1],[.07,.13])
    assert a['math-0']['label'].get_text()=='0.10'
    plt.close(fig)

def test_color_transfer_reaches_bars_and_value_labels():
    config,rows=case();config['palette']['cue']={'fill':'#86c6ba','edge':'#347f71','label':'#1f574e'}
    fig,a=build_figure(config,rows)
    np.testing.assert_allclose(a['math-1']['bar'].get_facecolor(),to_rgba('#86c6ba'))
    assert a['math-1']['label'].get_color()=='#1f574e'
    plt.close(fig)

@pytest.mark.parametrize('orientation',['vertical','horizontal'])
def test_automatic_layout_and_unequal_groups(orientation):
    rows=[{'id':str(i),'panel':'one','group':'large' if i<3 else 'small',
           'series':['base','cue','rl','base'][i],'value':v} for i,v in enumerate([.1,.4,.2,.7])]
    config={'panels':[{'id':'one'}],'panel_defaults':{'orientation':orientation}}
    fig,a=build_figure(config,rows)
    assert len(a)==4
    assert a['3']['x']-a['2']['x'] > a['1']['x']-a['0']['x']
    for i,v in enumerate([.1,.4,.2,.7]):
        bar=a[str(i)]['bar']
        assert (bar.get_height() if orientation=='vertical' else bar.get_width())==v
    plt.close(fig)

def test_missing_intervals_do_not_get_invented():
    config,rows=case()
    for row in rows:row.pop('low');row.pop('high')
    fig,a=build_figure(config,rows)
    assert all(item['error'] is None for item in a.values())
    plt.close(fig)

@pytest.mark.parametrize('name,count',[('cue-comparison',30),('data-edit',9),('teaser-strip',6),
                                      ('zero-shot-execution',45),('affordance-distribution',8),('planning-gains',4)])
def test_all_examples_export_with_bundled_and_system_fonts(name,count,tmp_path):
    config,rows=case(name)
    # No private fonts, reference PDFs or network access are used here.
    with warnings.catch_warnings():
        warnings.filterwarnings('error',message='Glyph .* missing')
        assert render(config,rows,tmp_path/name)==count
    for ext in ('png','pdf','svg'):assert (tmp_path/name).with_suffix('.'+ext).stat().st_size>1000

@pytest.mark.parametrize('change',[{'value':'nan'},{'low':'.8','high':'.2'},{'low':'.2','high':''}])
def test_invalid_numeric_inputs_fail(change,tmp_path):
    row={'id':'x','panel':'p','group':'g','series':'base','value':'.5','low':'.4','high':'.6'};row.update(change)
    p=tmp_path/'data.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    with pytest.raises(ValueError):load_data(p)

def test_clipping_requires_explicit_choice():
    config,rows=case();rows[0]['high']=1.2
    with pytest.raises(ValueError,match='clip data'):build_figure(config,rows)

def test_unknown_panel_is_not_silently_omitted():
    config,rows=case();rows[0]['panel']='unknown'
    with pytest.raises(ValueError,match='match configured'):build_figure(config,rows)

def test_pathological_grid_is_rejected_before_allocating_mesh():
    config,rows=case('data-edit')
    config['panels'][0]['style']['grid']['spacing_pt']=.001
    with pytest.raises(ValueError,match='too dense'):build_figure(config,rows)


def test_vertical_only_annotations_reject_horizontal_conversion():
    config,rows=case('teaser-strip')
    config['panels'][0]['style']['orientation']='horizontal'
    with pytest.raises(ValueError,match='require vertical'):build_figure(config,rows)

def test_overrides_are_typed_and_unknown_parameter_rejected():
    config=merge(DEFAULTS,{})
    apply_override(config,'panel_defaults.bar_width=0.9')
    assert config['panel_defaults']['bar_width']==.9
    with pytest.raises(ValueError):apply_override(config,'panel_defaults.bra_width=0.9')


def test_bare_override_value_is_a_string_and_json_keeps_its_type():
    config=merge(DEFAULTS,{})
    # PowerShell arrives without the quotes: tokens.mode="raw" -> tokens.mode=raw
    apply_override(config,'panel_defaults.tokens.mode=raw')
    apply_override(config,'panel_defaults.value_labels=false')
    apply_override(config,'panel_defaults.value_size=9')
    assert config['panel_defaults']['tokens']['mode']=='raw'
    assert config['panel_defaults']['value_labels'] is False
    assert config['panel_defaults']['value_size']==9


def test_stripped_json_override_points_to_set_file():
    config=merge(DEFAULTS,{})
    with pytest.raises(ValueError,match='set-file'):
        apply_override(config,'palette.cue={fill:#86c6ba}')


def test_override_file_merges_nested_values_without_mutating_base(tmp_path):
    config=merge(DEFAULTS,{})
    path=tmp_path/'overrides.json'
    path.write_text(json.dumps({'palette':{'cue':{'fill':'#86c6ba'}},
                                'panel_defaults':{'value_size':9}}),encoding='utf8')
    merged=apply_override_file(config,path)
    assert merged['palette']['cue']['fill']=='#86c6ba'
    assert merged['panel_defaults']['value_size']==9
    assert config['palette']['cue']['fill']=='#fabc00'


def test_override_file_rejects_unknown_parameter(tmp_path):
    config=merge(DEFAULTS,{})
    path=tmp_path/'overrides.json'
    path.write_text('{"panel_defaults": {"bra_width": 0.9}}',encoding='utf8')
    with pytest.raises(ValueError,match='Unknown parameter'):
        apply_override_file(config,path)


def test_group_labels_are_centered_and_legend_matches_series():
    config,rows=case('zero-shot-execution');fig,a=build_figure(config,rows);ax=fig.axes[0]
    assert [t.get_text() for t in ax.get_xticklabels()]==[f'Task {i}-{j}' for i in range(1,4) for j in range(1,4)]
    centers=[np.mean([v['x'] for key,v in a.items() if key.startswith(f'task-{i}-')]) for i in range(1,10)]
    np.testing.assert_allclose(ax.get_xticks(),centers)
    assert len(ax.get_legend().get_texts())==5
    zero=next(r for r in rows if r['value']==0)
    bar=a[zero['id']]['bar']
    assert bar.get_y()+bar.get_height()==pytest.approx(0)


def test_horizontal_percentage_labels_follow_replaced_values():
    config,rows=case('affordance-distribution');rows[0]['value']=.421
    fig,a=build_figure(config,rows)
    assert a['grasp']['bar'].get_width()==pytest.approx(.421)
    assert a['grasp']['label'].get_text()=='42.1%'
    assert fig.axes[0].yaxis_inverted()
    assert [t.get_text() for t in fig.axes[0].get_yticklabels()][0]=='grasp'


def test_gain_arrow_and_value_update_from_csv():
    config,rows=case('planning-gains')
    fig,a=build_figure(config,rows)
    key='gain-integrated-before-integrated-after'
    old=fig.findobj(lambda obj:obj.get_gid()==key+'-arrow')[0].get_path().vertices.copy()
    assert fig.findobj(lambda obj:obj.get_gid()==key+'-label')[0].get_text()=='+5.8'
    next(r for r in rows if r['id']=='integrated-after')['value']=80
    fig,a=build_figure(config,rows)
    assert fig.findobj(lambda obj:obj.get_gid()==key+'-label')[0].get_text()=='+6.7'
    new=fig.findobj(lambda obj:obj.get_gid()==key+'-arrow')[0].get_path().vertices
    assert not np.allclose(old,new)
    assert a['integrated-after']['bar'].get_y()==70
    assert a['integrated-after']['bar'].get_height()==10


@pytest.mark.parametrize('name',['cue-comparison','data-edit','teaser-strip'])
def test_readable_tokens_default_and_literal_opt_in(name):
    config,rows=case(name);fig,_=build_figure(config,rows)
    from matplotlib.text import Text
    texts=[t.get_text() for t in fig.findobj(Text)]
    assert not any(r'\n' in t or '\u2423' in t for t in texts)
    assert 'Okay' in texts
    config.setdefault('panel_defaults',{}).setdefault('tokens',{})['mode']='raw'
    fig,_=build_figure(config,rows)
    assert any(r'\n' in t.get_text() for t in fig.findobj(Text))


def test_legend_cannot_silently_omit_series():
    config,rows=case('zero-shot-execution');config['panels'][0]['legend']['order']=['dp3']
    with pytest.raises(ValueError,match='each plotted series'):build_figure(config,rows)


def test_auto_limits_accept_counts_without_manual_limits():
    rows=[{'id':'a','panel':'p','group':'A','series':'base','value':123.0},
          {'id':'b','panel':'p','group':'B','series':'base','value':45.0}]
    fig,_=build_figure({'panels':[{'id':'p'}]},rows)
    ax=fig.axes[0]
    assert ax.get_ylim()[0]==0
    assert ax.get_ylim()[1]>=123
    assert all(ax.get_ylim()[0] <= tick <= ax.get_ylim()[1] for tick in ax.get_yticks())


def test_auto_limits_include_intervals_and_explicit_limits_win():
    rows=[{'id':'a','panel':'p','group':'A','series':'base','value':1.0,'low':.9,'high':1.4}]
    fig,_=build_figure({'panels':[{'id':'p'}]},rows)
    assert fig.axes[0].get_ylim()[1]>=1.4
    fig,_=build_figure({'panels':[{'id':'p'}],'panel_defaults':{'limits':[0,2]}},rows)
    assert fig.axes[0].get_ylim()==(0.0,2.0)


def test_reference_line_and_label_are_drawn():
    rows=[{'id':'a','panel':'p','group':'A','series':'base','value':.8}]
    config={'panels':[{'id':'p'}],'panel_defaults':{'reference_lines':[
        {'value':.8,'label':'SOTA','color':'#6B7280'}]}}
    fig,_=build_figure(config,rows)
    ax=fig.axes[0]
    assert any(np.allclose(line.get_ydata(),[.8,.8]) for line in ax.lines)
    assert any(text.get_text()=='SOTA' for text in ax.texts)


def test_grid_lines_can_target_both_axes():
    rows=[{'id':'a','panel':'p','group':'A','series':'base','value':.6}]
    config={'panels':[{'id':'p'}],'panel_defaults':{'grid':{'kind':'lines','axis':'both'}}}
    fig,_=build_figure(config,rows)
    ax=fig.axes[0]
    assert any(line.get_visible() for line in ax.xaxis.get_gridlines())
    assert any(line.get_visible() for line in ax.yaxis.get_gridlines())


def test_fixed_panel_rectangles_do_not_require_auto_grid():
    panels=[{'id':str(i),'rect_pt':[i*10,0,10,10]} for i in range(5)]
    config={'figure':{'size_pt':[360,210]},'layout':{'columns':1},'panels':panels}
    assert len(list(panel_rectangles(config)))==5


def test_svg_text_is_editable_by_default(tmp_path):
    rows=[{'id':'a','panel':'p','group':'A','series':'base','value':.5}]
    config={'figure':{'formats':['svg']},'panels':[{'id':'p'}]}
    render(config,rows,tmp_path/'text')
    assert '<text' in (tmp_path/'text.svg').read_text(encoding='utf8')
    config['figure']['svg_text']=False
    render(config,rows,tmp_path/'paths')
    assert '<text' not in (tmp_path/'paths.svg').read_text(encoding='utf8')


def test_frozen_replica_rejects_style_but_accepts_palette(tmp_path):
    script=Path(__file__).resolve().parent/'render.py'
    config=EXAMPLES/'cue-comparison/config.json'
    rejected=subprocess.run([sys.executable,str(script),'--config',str(config),
                             '--style','soft-outline','--output',str(tmp_path/'x')],
                            capture_output=True,text=True,encoding='utf8')
    assert rejected.returncode!=0
    assert 'measured panel geometry' in (rejected.stderr+rejected.stdout)
    snapshot=tmp_path/'resolved.json'
    subprocess.run([sys.executable,str(script),'--config',str(config),'--palette','tol-bright',
                    '--resolved-config',str(snapshot),'--output',str(tmp_path/'ok')],
                   check=True,capture_output=True,text=True,encoding='utf8')
    resolved=json.loads(snapshot.read_text(encoding='utf8'))
    assert resolved['palette']['base']['fill']=='#4477AA'


@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
def test_capacity_hollow_and_solid_geometry_labels_and_axis(orientation):
    rows = [{"id": "done", "panel": "p", "group": "A", "series": "base", "value": 88., "capacity": 96.}]
    config = {"panels": [{"id": "p"}], "layout": {"right_pt": 110}, "panel_defaults": {"orientation": orientation,
              "capacity": {"field": "capacity"}, "value_format": ".0f"}}
    fig, artists = build_figure(config, rows)
    item = artists["done"]
    hollow, solid = item["capacity_bar"], item["bar"]
    extent = lambda p: p.get_height() if orientation == "vertical" else p.get_width()
    assert extent(hollow) == 96
    assert extent(solid) == 88
    assert hollow.get_facecolor()[3] == 0
    assert hollow.get_zorder() == 1 and solid.get_zorder() == 2
    assert hollow.get_linestyle() == "--"
    assert hollow.get_alpha() == .45
    assert item["label"].get_text() == "88"
    assert item["capacity_label"].get_text() == "88 / 96 (92%)"
    assert (fig.axes[0].get_ylim() if orientation == "vertical" else fig.axes[0].get_xlim())[1] >= 96


def test_capacity_nonzero_baseline_and_custom_label():
    rows = [{"id": "a", "panel": "p", "group": "A", "series": "base", "value": 88., "capacity": 96.}]
    cfg = {"panels": [{"id": "p"}], "panel_defaults": {"baseline": 70,
           "capacity": {"field": "capacity", "label_format": "{value:.0f} of {capacity:.0f}", "show_percent": False}}}
    _, artists = build_figure(cfg, rows)
    assert artists["a"]["bar"].get_y() == 70
    assert artists["a"]["bar"].get_height() == 18
    assert artists["a"]["capacity_bar"].get_height() == 26
    assert artists["a"]["capacity_label"].get_text() == "88 of 96"


@pytest.mark.parametrize("change, message", [
    ({"capacity": 80.}, "capacity >= value"),
    ({"capacity": float("nan")}, "capacity"),
    ({"low": 80., "high": 90.}, "Interval.*capacity"),
])
def test_capacity_rejects_invalid_semantics(change, message):
    row = {"id": "a", "panel": "p", "group": "A", "series": "base", "value": 88., "capacity": 96.}
    row.update(change)
    with pytest.raises(ValueError, match=message):
        build_figure({"panels": [{"id": "p"}], "panel_defaults": {"capacity": {"field": "capacity"}}}, [row])


def test_capacity_mixed_panel_rows_fail_even_when_disabled():
    rows = [{"id": "a", "panel": "p", "group": "A", "series": "base", "value": 88., "capacity": 96.},
            {"id": "b", "panel": "p", "group": "B", "series": "base", "value": 70.}]
    with pytest.raises(ValueError, match="all rows"):
        build_figure({"panels": [{"id": "p"}]}, rows)


@pytest.mark.parametrize("style, message", [
    ({"limits": [0, 90]}, "clip capacity"),
    ({"baseline": 90}, "capacity >= value >= baseline"),
])
def test_capacity_axis_and_baseline_validation(style, message):
    rows = [{"id": "a", "panel": "p", "group": "A", "series": "base", "value": 88., "capacity": 96.}]
    with pytest.raises(ValueError, match=message):
        build_figure({"panels": [{"id": "p"}], "panel_defaults": style}, rows)


def test_capacity_csv_parsing_and_interval_conflict(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("id,panel,group,series,value,capacity\na,p,A,base,88,96\n")
    assert load_data(path)[0]["capacity"] == 96.
    path.write_text("id,panel,group,series,value,capacity,low,high\na,p,A,base,88,96,80,90\n")
    with pytest.raises(ValueError, match="Interval.*capacity"):
        load_data(path)


def test_zero_capacity_has_no_fabricated_percentage():
    row = {"id": "a", "panel": "p", "group": "A", "series": "base", "value": 0., "capacity": 0.}
    _, artists = build_figure({"panels": [{"id": "p"}],
                              "panel_defaults": {"capacity": {"field": "capacity"}}}, [row])
    assert artists["a"]["capacity_label"].get_text() == "0 / 0 (n/a)"


def increment_case(base=60., value=90., baseline=10.):
    rows = [{"id": "a", "panel": "p", "group": "A", "series": "base", "base": base, "value": value}]
    cfg = {"figure": {"size_pt": [360, 240]}, "layout": {"columns": 1, "top_pt": 40},
           "panels": [{"id": "p"}],
           "panel_defaults": {"baseline": baseline, "increment": {"field": "base"}, "grid": {"kind": "none"}}}
    return cfg, rows


def test_increment_segments_total_metadata_and_labels():
    cfg, rows = increment_case()
    fig, a = build_figure(cfg, rows)
    item = a["a"]
    assert item["base_bar"].get_height() == 50
    assert item["increment_bar"].get_height() == 30
    assert item["base_bar"].get_height() + item["increment_bar"].get_height() == 90 - 10
    assert item["base_bar"].get_hatch() == "////"
    assert not item["increment_bar"].get_hatch()
    assert not item["bar"].get_visible()
    assert item["bar"].get_y() == 10 and item["bar"].get_height() == 80
    assert item["label"] is item["total_label"]
    assert item["total_label"].get_text() == "90"
    assert item["increment_label"].get_text() == "+30"
    assert item["increment_label_inside"]
    assert item["increment_leader"] is None
    assert item["increment_separator"].get_linewidth() == 1.5
    assert fig.axes[0].get_ylim()[1] >= 90


def test_tiny_increment_label_uses_leader_without_hiding_total():
    cfg, rows = increment_case(base=89.99)
    cfg["panel_defaults"]["limits"] = [0, 120]
    fig, a = build_figure(cfg, rows)
    item = a["a"]
    assert not item["increment_label_inside"]
    assert item["increment_leader"] is not None
    renderer = fig.canvas.get_renderer()
    assert not item["total_label"].get_window_extent(renderer).overlaps(item["increment_label"].get_window_extent(renderer))


@pytest.mark.parametrize("change, message", [
    ({"base": 91}, "0 <= base <= value"),
    ({"base": -1}, "0 <= base <= value"),
    ({"base": float("nan")}, "finite"),
    ({"value": float("inf")}, "finite"),
    ({"low": 80, "high": 95}, "intervals or capacity"),
    ({"capacity": 100}, "intervals or capacity"),
])
def test_increment_invalid_data_rejected(change, message):
    cfg, rows = increment_case()
    rows[0].update(change)
    with pytest.raises(ValueError, match=message):
        build_figure(cfg, rows)


def test_increment_horizontal_and_missing_base_rejected():
    cfg, rows = increment_case()
    cfg["panel_defaults"]["orientation"] = "horizontal"
    with pytest.raises(ValueError, match="vertical.*horizontal"):
        build_figure(cfg, rows)
    cfg["panel_defaults"]["orientation"] = "vertical"
    cfg["panel_defaults"]["increment"]["field"] = None
    rows.append({"id": "b", "panel": "p", "group": "B", "series": "base", "value": 80})
    with pytest.raises(ValueError, match="all rows must supply base"):
        build_figure(cfg, rows)


def test_increment_csv_base_parsed_and_validated(tmp_path):
    path = tmp_path / "base.csv"
    path.write_text("id,panel,group,series,base,value\na,p,A,base,60,90\n")
    assert load_data(path)[0]["base"] == 60.
    path.write_text("id,panel,group,series,base,value\na,p,A,base,91,90\n")
    with pytest.raises(ValueError, match="0 <= base <= value"):
        load_data(path)

def delta_case(values, groups=None, reverse=False, **gain_defaults):
    groups = groups or ['pair'] * len(values)
    rows = [{'id': str(i), 'panel': 'p', 'group': group, 'series': 'base', 'value': value}
            for i, (value, group) in enumerate(zip(values, groups))]
    pairs = [(str(i), str(i+1)) for i in range(0, len(rows), 2)]
    config = {'panels': [{'id': 'p'}],
              'panel_defaults': {'position_mode': 'auto', 'value_format': '.1f'},
              'gain_defaults': gain_defaults,
              'gains': [{'from': b if reverse else a, 'to': a if reverse else b}
                        for a, b in pairs]}
    return config, rows


def delta_geometry(fig, artists):
    """Inspect the rendered shaft AND arrowhead independently of routing helpers."""
    renderer = fig.canvas.get_renderer()
    scale = 72 / fig.dpi
    for item in artists.values():
        for gain in item.get('auto_gains', []):
            arrow = gain['arrow']
            rendered = arrow.get_transform().transform_path(arrow.get_path())
            samples = []
            for curve, code in rendered.iter_bezier():
                if code != rendered.CLOSEPOLY:
                    samples.extend(curve(np.linspace(0, 1, 101)))
            points = np.asarray(samples) * scale
            label = gain['label'].get_window_extent(renderer).transformed(
                Affine2D().scale(scale))
            panel = item['axis'].get_window_extent(renderer).transformed(
                Affine2D().scale(scale))
            assert len(points) >= 40
            assert np.all(points[:, 0] > panel.x0) and np.all(points[:, 0] < panel.x1)
            assert np.all(points[:, 1] > panel.y0) and np.all(points[:, 1] < panel.y1)
            assert panel.x0 < label.x0 < label.x1 < panel.x1
            assert panel.y0 < label.y0 < label.y1 < panel.y1
            for other in artists.values():
                if other['axis'] is not item['axis']:
                    continue
                for key in ('bar', 'capacity_bar', 'label', 'capacity_label', 'increment_label'):
                    artist = other.get(key)
                    if artist is None:
                        continue
                    box = artist.get_window_extent(renderer).transformed(
                        Affine2D().scale(scale)).padded(1)
                    assert not np.any((points[:, 0] >= box.x0) & (points[:, 0] <= box.x1) &
                                      (points[:, 1] >= box.y0) & (points[:, 1] <= box.y1)), key
                    assert not label.overlaps(box), key
            yield item, gain, label, points


@pytest.mark.parametrize('values', [(40, 80), (80, 40), (79.8, 80), (80, 79.8)])
@pytest.mark.parametrize('reverse', [False, True])
def test_auto_delta_ascending_descending_and_small_changes(values, reverse):
    config, rows = delta_case(values, reverse=reverse)
    fig, artists = build_figure(config, rows)
    results = list(delta_geometry(fig, artists))
    assert len(results) == 1
    _, gain, _, _ = results[0]
    expected = (values[0]-values[1]) if reverse else (values[1]-values[0])
    assert gain['label'].get_text() == format(expected, '+.1f')
    assert gain['leader'] is not None  # Outside-of-pair placement stays associated.


def test_auto_delta_labels_stay_in_their_adjacent_group_slots():
    config, rows = delta_case([50, 51, 75, 60, 50, 80], ['a', 'a', 'b', 'b', 'c', 'c'])
    fig, artists = build_figure(config, rows)
    scale = 72/fig.dpi
    results = list(delta_geometry(fig, artists))
    assert len(results) == 3
    boundaries = [(artists[str(i)]['bar'].get_window_extent().x1 +
                   artists[str(i+1)]['bar'].get_window_extent().x0)*scale/2 for i in (1, 3)]
    for (_, _, label, _), left, right in zip(results, [-np.inf]+boundaries, boundaries+[np.inf]):
        assert left < label.x0 < label.x1 < right


@pytest.mark.parametrize('anchor', ['left', 'center', 'right'])
def test_auto_delta_tracks_current_bar_width_and_anchor(anchor):
    config, rows = delta_case([50, 80], tail_anchor=anchor, tip_anchor=anchor)
    for width in (.3, 1.1):
        config['panel_defaults']['bar_width'] = width
        fig, artists = build_figure(config, rows)
        gain = artists['0']['auto_gains'][0]
        box = artists['1']['bar'].get_window_extent()
        expected = {'left': box.x0, 'center': (box.x0+box.x1)/2, 'right': box.x1}[anchor]
        assert gain['path_pt'].vertices[-1, 0] == pytest.approx(expected*72/fig.dpi)
        list(delta_geometry(fig, artists))


def test_auto_delta_fixed_limits_report_insufficient_room():
    config, rows = delta_case([50, 80])
    config['panel_defaults']['limits'] = [0, 80]
    with pytest.raises(ValueError, match='increase y_max or figure height'):
        build_figure(config, rows)


@pytest.mark.parametrize('name', ['cue-comparison', 'data-edit', 'teaser-strip',
                                  'zero-shot-execution', 'affordance-distribution', 'planning-gains'])
def test_frozen_gain_geometry_defaults_to_legacy(name):
    config, rows = case(name)
    fig, _ = build_figure(config, rows)
    config.setdefault('gain_defaults', {})['auto_layout'] = False
    legacy, _ = build_figure(config, rows)
    def geometry(figure):
        result = {}
        for artist in figure.findobj():
            gid = artist.get_gid() or ''
            if gid.startswith('gain-'):
                result[gid] = (artist.get_path().vertices if gid.endswith('-arrow')
                               else np.array(artist.get_position()))
        return result
    actual, expected = geometry(fig), geometry(legacy)
    assert actual.keys() == expected.keys()
    for key in actual:
        np.testing.assert_array_equal(actual[key], expected[key])
    # Captured before this capability task; detects changes in the legacy branch too.
    snapshot = json.loads((Path(__file__).parent/'fixtures/frozen-gains.json').read_text())[name]
    assert actual.keys() == snapshot.keys()
    for key, captured in snapshot.items():
        coordinates = captured['position'] if key.endswith('-label') else captured
        np.testing.assert_allclose(actual[key], coordinates, rtol=0, atol=1e-12)
        if key.endswith('-label'):
            label = fig.findobj(lambda artist: artist.get_gid() == key)[0]
            assert label.get_text() == captured['text']

@pytest.mark.parametrize('encoding', ['capacity', 'increment'])
def test_auto_delta_respects_capacity_and_increment_labels(encoding):
    config, rows = delta_case([50, 80])
    if encoding == 'capacity':
        rows[0]['capacity'], rows[1]['capacity'] = 60, 90
        config['panel_defaults']['capacity'] = {'field': 'capacity'}
    else:
        rows[0]['base'], rows[1]['base'] = 45, 79.8
        config['panel_defaults']['increment'] = {'field': 'base'}
    fig, artists = build_figure(config, rows)
    assert len(list(delta_geometry(fig, artists))) == 1
