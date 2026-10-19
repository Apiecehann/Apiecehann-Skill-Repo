"""Behaviour checks: changed data, different groups, intervals and style overrides."""
import csv
import json
import warnings
from pathlib import Path
import numpy as np
import pytest
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from render import (DEFAULTS, build_figure, load_data, merge, apply_override,
                    apply_override_file, render)

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
