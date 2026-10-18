"""Preset migration, opacity independence and portable command-line behavior."""
import copy
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np
import pytest

from render import build_figure, load_data, read_config, resolve_config, preset_catalog, apply_override, render
from catalog import compose_board

SCRIPTS = Path(__file__).resolve().parent
GUIDE = SCRIPTS.parent/'examples/style-guide'


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def recipe(name='config.json'):
    config = read_config(GUIDE/name)
    return config,load_data(GUIDE/config['data'])


@pytest.mark.parametrize('style',['paper-clean','soft-outline','serif-emphasis'])
@pytest.mark.parametrize('name',['config.json','horizontal.json','paired.json','two-series.json'])
def test_styles_transfer_across_layouts_without_changing_data(style,name):
    config,rows = recipe(name)
    config['preset']['style'] = style
    original = copy.deepcopy((config,rows))
    with warnings.catch_warnings():
        warnings.filterwarnings('error',message='Glyph .* missing')
        fig,artists = build_figure(config,rows)
    assert (config,rows) == original
    assert len(artists) == len(rows)
    for row in rows:
        item = artists[row['id']]
        bar = item['bar']
        start,size = (bar.get_y(),bar.get_height()) if item['vertical'] else (bar.get_x(),bar.get_width())
        assert start+size == pytest.approx(row['value'])
        assert item['error'] is None
    axis = fig.axes[0]
    assert (axis.get_ylim() if artists[rows[0]['id']]['vertical'] else axis.get_xlim()) == tuple(config['panel_defaults']['limits'])


def test_fill_alpha_does_not_fade_edge_text_error_or_legend():
    config,rows = recipe()
    config['preset']['style'] = 'soft-outline'
    config['panel_defaults'].update(bar_fill_alpha=.25,bar_edge_alpha=.9,value_labels=True,value_alpha=.8,error_alpha=.7)
    config['palette'] = {'dp3':{'fill_alpha':.4,'edge_alpha':1,'label_alpha':1}}
    rows[0].update(low=.7,high=.9)
    fig,artists = build_figure(config,rows)
    item = artists[rows[0]['id']]
    assert item['bar'].get_alpha() is None
    assert item['bar'].get_facecolor()[3] == .4
    assert item['bar'].get_edgecolor()[3] == 1
    assert item['label'].get_alpha() == 1
    assert item['error'].lines[2][0].get_alpha() == .7
    other = artists[rows[1]['id']]
    assert other['bar'].get_facecolor()[3] == .25
    assert other['bar'].get_edgecolor()[3] == .9
    assert other['label'].get_alpha() == .8
    assert all(text.get_alpha() == 1 for text in fig.axes[0].get_xticklabels())
    patches = fig.axes[0].get_legend().get_patches()
    np.testing.assert_allclose(patches[0].get_facecolor(),item['bar'].get_facecolor())
    np.testing.assert_allclose(patches[0].get_edgecolor(),item['bar'].get_edgecolor())


def test_legacy_alpha_fades_both_bar_parts():
    rows = [{'id':'a','panel':'p','group':'g','series':'base','value':.4}]
    config = {'panels':[{'id':'p'}],'panel_defaults':{'bar_alpha':.3}}
    _,artists = build_figure(config,rows)
    assert artists['a']['bar'].get_facecolor()[3] == .3
    assert artists['a']['bar'].get_edgecolor()[3] == .3


@pytest.mark.parametrize('alpha',[-.01,1.01,float('nan')])
def test_invalid_opacity_fails_explicitly(alpha):
    config,rows = recipe()
    config['panel_defaults']['bar_fill_alpha'] = alpha
    with pytest.raises(ValueError,match='between 0 and 1'):
        build_figure(config,rows)


def test_selection_order_and_explicit_overrides():
    config,rows = recipe()
    config['preset']['style'] = 'soft-outline'
    config['panel_defaults']['bar_fill_alpha'] = .8
    config['panels'] = [{'id':'tasks','style':{'bar_fill_alpha':.6}}]
    resolved = resolve_config(config,rows)
    apply_override(resolved,'palette.dp3.fill_alpha=0.2')
    _,artists = build_figure(resolved,rows)
    assert artists[rows[0]['id']]['bar'].get_facecolor()[3] == .2
    assert artists[rows[1]['id']]['bar'].get_facecolor()[3] == .6
    shuffled = resolve_config(config,list(reversed(rows)))
    assert shuffled['palette'] == resolve_config(config,rows)['palette']


def test_semantic_palette_requires_and_respects_roles():
    config,rows = recipe()
    config['preset']['palette'] = 'gray-purple'
    with pytest.raises(ValueError,match='series_roles'): resolve_config(config,rows)
    config['series_roles'] = dict(zip(config['series_order'],['baseline-1','baseline-2','baseline-3','focus-secondary','focus']))
    resolved = resolve_config(config,rows)
    assert resolved['palette']['saga-point']['fill'] == '#9979CB'
    assert resolve_config(config,rows[5:])['palette'] == resolved['palette']


def test_palette_does_not_silently_cycle():
    config,rows = recipe()
    config['preset']['palette'] = 'blue-orange'
    with pytest.raises(ValueError,match='at most 2'): resolve_config(config,rows)
    config['preset']['palette'] = 'unknown'
    with pytest.raises(ValueError,match='Unknown palettes'): resolve_config(config,rows)


def test_auto_spacing_can_be_overridden_by_explicit_positions():
    config,rows = recipe()
    _,auto = build_figure(config,rows)
    assert auto[rows[0]['id']]['x'] == 0
    config['panel_defaults'].update(position_mode='data',bar_width=14)
    _,fixed = build_figure(config,rows)
    assert fixed[rows[0]['id']]['x'] == rows[0]['x']


def test_gain_tip_tracks_the_bar_edge_when_width_changes():
    config,rows = recipe('paired.json')
    for width in (.5,1.2):
        config['panel_defaults']['bar_width'] = width
        fig,artists = build_figure(config,rows)
        target = artists['integrated-after']
        edge = fig.transFigure.inverted().transform(target['axis'].transData.transform((target['bar'].get_x(),target['value'])))[0]
        arrow = fig.findobj(lambda artist:artist.get_gid()=='gain-integrated-before-integrated-after-arrow')[0]
        assert arrow.get_path().vertices[:,0].max() < edge


@pytest.mark.parametrize('board_index',range(5))
def test_comparison_pages_export_vectors_without_missing_glyphs(board_index,tmp_path):
    board = json.loads((GUIDE/'gallery.json').read_text(encoding='utf8'))['boards'][board_index]
    config,rows = compose_board(board,GUIDE)
    with warnings.catch_warnings():
        warnings.filterwarnings('error',message='Glyph .* missing')
        render(config,rows,tmp_path/board['name'])
    assert '<image' not in (tmp_path/(board['name']+'.svg')).read_text(encoding='utf8')
    assert b'/Subtype /Image' not in (tmp_path/(board['name']+'.pdf')).read_bytes()


def test_cli_selection_and_resolved_config_replay(tmp_path):
    output = tmp_path/'selected'
    snapshot = tmp_path/'resolved.json'
    command = [sys.executable,str(SCRIPTS/'render.py'),'--config',str(GUIDE/'config.json'),
               '--style','soft-outline','--font','serif','--output',str(output),'--resolved-config',str(snapshot)]
    subprocess.run(command,check=True,capture_output=True,text=True,encoding='utf8')
    config = read_config(snapshot)
    assert config['resolved_preset']['style'] == 'soft-outline'
    assert config['resolved_preset']['font'] == 'serif'
    assert Path(config['data']).is_file()
    assert config == resolve_config(config,load_data(config['data']))
    subprocess.run([sys.executable,str(SCRIPTS/'render.py'),'--config',str(snapshot),
                    '--output',str(tmp_path/'replayed')],cwd=tmp_path,check=True,capture_output=True)
    assert (tmp_path/'selected.png').read_bytes() == (tmp_path/'replayed.png').read_bytes()


def test_catalog_cli_embeds_fonts_and_preserves_vector_pages(tmp_path):
    subprocess.run([sys.executable,str(SCRIPTS/'catalog.py'),'--config',str(GUIDE/'gallery.json'),
                    '--output',str(tmp_path)],check=True,capture_output=True)
    pdf = (tmp_path/'catalog.pdf').read_bytes()
    assert len(re.findall(rb'/Type /Page\b',pdf)) == 5
    assert b'/Subtype /Type3' not in pdf
    assert b'/FontFile2' in pdf
    assert b'/Subtype /Image' not in pdf
