"""Independent anchors and actual rendered artists for the palette study."""
import copy
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, to_hex
import numpy as np
import pytest

from palette_audit import composite, contrast, evaluate, separation, simulate, study_board
from render import build_figure, load_data

ROOT=Path(__file__).parents[3]/'reference/legacy-grouped-bar/examples/palette-study'
SETTINGS=json.loads((ROOT/'config.json').read_text(encoding='utf8'))
CANDIDATES=json.loads((ROOT/'candidates.json').read_text(encoding='utf8'))


def test_known_srgb_contrast_anchors():
    assert contrast([0,0,0],[1,1,1]) == pytest.approx(21)
    assert contrast([1,1,1],[1,1,1]) == pytest.approx(1)
    assert contrast(to_rgb('#777777'),[1,1,1]) == pytest.approx(4.47808945)


def test_composite_and_simulation_neutral_anchors():
    assert composite(['#000000'],.25).tolist() == [[.75,.75,.75]]
    for mode in ('normal','protanomaly','deuteranomaly','tritanomaly','grayscale'):
        np.testing.assert_allclose(simulate(np.array([[.5,.5,.5]]),mode),[[.5,.5,.5]],atol=2e-6)
    assert separation([[.2,.4,.6],[.2,.4,.6]])[0] == 0


def test_candidate_count_does_not_count_aliases_as_new_sets():
    assert len(CANDIDATES)==100
    sets={tuple(sorted(c.lower() for c in x['colors'])) for x in CANDIDATES}
    assert len(sets)==50
    for first,second in zip(CANDIDATES[::2],CANDIDATES[1::2]):
        assert first['colors']==second['colors']
        assert [first['fill_alpha'],second['fill_alpha']]==[1,.72]


def test_near_duplicate_palette_is_flagged():
    candidate=copy.deepcopy(CANDIDATES[0])
    candidate['colors']=['#334455','#334456','#334457','#334458','#334459']
    result=evaluate(candidate,SETTINGS)
    assert 'normal-neighbours' in result['flags_3']
    assert 'cvd-neighbours' in result['flags_5']


def test_three_series_diagnostics_ignore_unused_fourth_and_fifth_colours():
    candidate=copy.deepcopy(CANDIDATES[0])
    candidate['colors']=candidate['colors'][:3]+['#ffffff','#fffffe']
    result=evaluate(candidate,SETTINGS)
    assert 'near-white-fill' not in result['flags_3']
    assert 'near-white-fill' in result['flags_5']


def test_layered_preview_preserves_heights_and_does_not_double_composite():
    candidate=CANDIDATES[1]
    rows=load_data(ROOT/'data.csv')
    config,data=study_board([candidate],rows,SETTINGS,'Test')
    fig,artists=build_figure(config,data)
    try:
        top=artists['0-1-g1s1']['bar'];lower=artists['0-1-g1s1-lower']['bar']
        assert top.get_x()==lower.get_x()
        assert top.get_height()==.42
        assert lower.get_height()==.18
        assert lower.get_y()==0
        assert lower.get_hatch()=='////'
        assert top.get_hatch() is None
        assert top.get_facecolor()==lower.get_facecolor()
        expected=to_rgb(to_hex(composite(candidate['colors'],.72)[0]))
        np.testing.assert_allclose(top.get_facecolor(),[*expected,1])
        assert lower.get_edgecolor()==(*to_rgb(SETTINGS['outline']),1)
    finally:
        plt.close(fig)


def test_bad_inputs_are_rejected():
    with pytest.raises(ValueError): composite(['#ffffff'],1.1)
    with pytest.raises(ValueError): simulate(np.array([[0,0,0]]),'guess')
    with pytest.raises(ValueError): separation([[0,0,0]])
