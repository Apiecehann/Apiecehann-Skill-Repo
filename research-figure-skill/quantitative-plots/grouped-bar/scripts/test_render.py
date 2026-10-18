"""Behaviour checks: changed data, different groups, intervals and style overrides."""
import csv
import json
import warnings
from pathlib import Path
import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from render import DEFAULTS, build_figure, load_data, merge, apply_override, render

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

@pytest.mark.parametrize('name,count',[('cue-comparison',30),('data-edit',9),('teaser-strip',6)])
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
