"""Configurable grouped bars. Data, layout, typography and colour are separate.

Run with --config ../examples/cue-comparison/config.json. No reference image is
opened by this renderer: every bar, interval, grid point and label is generated.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
import math
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.text import Text
from matplotlib.textpath import TextToPath
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, FancyBboxPatch, FancyArrowPatch, Patch
import numpy as np

DEFAULTS = {
    'figure': {'size_pt': [540, 180], 'background': 'white', 'dpi': 300,
               'formats': ['png', 'pdf', 'svg'], 'svg_text': False},
    'fonts': {'light': {'family': ['Liberation Sans','Arial','DejaVu Sans'], 'weight': 'normal', 'file': 'Graphik-Light.ttf'},
              'regular': {'family': ['Liberation Sans','Arial','DejaVu Sans'], 'weight': 'normal', 'file': 'Graphik-Regular.ttf'},
              'mono': {'family': 'DejaVu Sans Mono', 'weight': 'normal', 'file': 'B612Mono-Regular.ttf'}},
    'palette': {'base': {'fill': '#a1a1a1', 'edge': '#525252', 'label': '#404040'},
                'cue': {'fill': '#fabc00', 'edge': '#da7700', 'label': '#b45300'},
                'rl': {'fill': '#56a2ff', 'edge': '#155dfc', 'label': '#1447e6'},
                'edit': {'fill': '#ff6568', 'edge': '#e40016', 'label': '#bf000f'},
                'answer': {'fill': '#a686ff', 'edge': '#7f22fe', 'label': '#7008e7'}},
    'panel_defaults': {
        'orientation': 'vertical', 'limits': [0, 1.07], 'ticks': [0, .2, .4, .6, .8, 1],
        'tick_format': '.1f', 'tick_size': 9.5, 'tick_length': 4, 'tick_width': .6,
        'tick_font': 'light', 'value_tick_length': None,
        'tick_pad': 3.5, 'tick_color': '#525252', 'text_color': '#111111',
        'axis_color': '#101828', 'axis_width': .6, 'baseline_width': .8,
        'spines': ['left','bottom'],
        'show_value_ticks': True, 'show_category_ticks': True, 'show_categories': True,
        'category_size': 7.6, 'category_pad': 6, 'category_rotation': 0,
        'category_mode': 'bar', 'category_font': 'light', 'invert_categories': False,
        'label_size': 11.5, 'label_pad': 4, 'ylabel': '',
        'label_font': 'regular',
        'bar_width': .55, 'bar_edge_width': .8, 'bar_alpha': 1, 'hatch': None,
        'bar_fill_alpha': None, 'bar_edge_alpha': None, 'position_mode': 'data',
        'group_gap': .8, 'series_gap': .45, 'category_margin': .35,
        'error_width': .7, 'error_color': '#111111', 'error_cap': 2,
        'error_alpha': 1, 'value_alpha': 1, 'text_alpha': 1,
        'value_labels': True, 'value_format': '.2f', 'value_size': 10.5,
        'value_font': 'light', 'value_color': None,
        'value_pad': 5, 'value_anchor': 'high', 'value_background': True,
        'value_background_pad': .1, 'baseline': 0, 'allow_interval_clipping': False,
        'grid': {'kind': 'dots', 'spacing_pt': 10.5, 'value_step': .1,
                 'value_stop': 1, 'size': .75, 'color': '#bdbdbd', 'alpha': 1, 'max_points': 50000,
                 'linewidth': .5, 'linestyle': '-'},
        'tokens': {'mode': 'readable', 'size': 6.3, 'gap': 2.6, 'padding_em': [.16, .16],
                   'height_em': 1.333333, 'baseline_em': .405, 'rounding': .194444,
                   'edge_width': .4, 'background': '#f5f5f5', 'edge': '#262626',
                   'shadow': True, 'shadow_offset': [.35, -.55], 'shadow_alpha': .28,
                   'offset_pt': 6, 'tint': False},
    },
    'legend_defaults': {'show': False, 'order': None, 'labels': {}, 'font': 'regular', 'size': 10,
                        'loc': 'upper center', 'anchor': [.5,1.2], 'columns': 3, 'frame': True,
                        'facecolor': 'white', 'edgecolor': '#cccccc', 'frame_alpha': 1,
                        'frame_width': .8, 'rounded': True, 'borderpad': .4,
                        'columnspacing': 2, 'handlelength': 2, 'handleheight': .7,
                        'handletextpad': .8, 'borderaxespad': .5},
    'gain_defaults': {'color': None, 'palette_part': 'edge', 'linewidth': 2.5,
                     'alpha': 1, 'label_alpha': 1,
                     'head_length_pt': 7, 'head_width_pt': 6, 'tail_pad_pt': 5, 'tip_pad_pt': 9,
                     'tail_dx_pt': -12, 'tip_dx_pt': -16,
                     'tail_anchor': 'center', 'tip_anchor': 'center',
                     'control1': [.55,0], 'control2': [.9,.55],
                     'label_position': [.5,.48], 'label_offset_pt': [-8,0],
                     'label_size': 15, 'label_font': 'regular', 'label_format': '+.1f',
                     'label_scale': 1, 'label_suffix': '', 'clip': False},
    'panels': [], 'annotations': [], 'bands': [], 'icons': [], 'gains': [],
    'layout': {'columns': 3, 'left_pt': 42, 'right_pt': 8, 'top_pt': 22,
               'bottom_pt': 38, 'column_gap_pt': 30, 'row_gap_pt': 32},
    'rc': {},
}


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result


@lru_cache(maxsize=1)
def preset_catalog():
    return json.loads((Path(__file__).parent/'presets.json').read_text(encoding='utf8'))


def resolve_config(config, rows):
    """Compose defaults < style < layout < palette/font < explicit configuration.

    Presets never set numeric limits, ticks, baselines or interval definitions.
    The six measured reference configurations still use the original path.
    """
    if 'preset' not in config:
        result = merge(DEFAULTS, config)
        for entry in result['palette'].values():
            for key in ('fill_alpha','edge_alpha','label_alpha'):
                entry.setdefault(key, None)
        return result
    catalog = preset_catalog()
    selection = config['preset']
    if not isinstance(selection, dict) or set(selection)-{'style','layout','palette','font'}:
        raise ValueError('preset accepts style, layout, palette and optional font')
    style_name = selection.get('style', 'paper-clean')
    layout_name = selection.get('layout', 'grouped')
    def pick(section, name):
        if name not in catalog[section]:
            raise ValueError(f'Unknown {section} preset {name!r}; choose from {list(catalog[section])}')
        return catalog[section][name]
    style = pick('styles', style_name)
    layout = pick('layouts', layout_name)
    palette_name = selection.get('palette', layout.get('palette', style['palette']))
    palette = pick('palettes', palette_name)
    font_name = selection.get('font', style['font'])
    typography = pick('fonts', font_name)
    result = merge(merge(DEFAULTS, style['config']), layout['config'])
    result['fonts'] = copy.deepcopy(typography['roles'])
    present = list(dict.fromkeys(row['series'] for row in rows))
    order = config.get('series_order', present)
    if not order or len(set(order)) != len(order) or not set(present).issubset(order):
        raise ValueError('series_order must be unique and include every plotted series')
    if palette['kind'] == 'categorical':
        if len(order) > len(palette['colors']):
            raise ValueError(f'{palette_name} supports at most {len(palette["colors"])} series; choose another palette')
        colors = dict(zip(order, palette['colors']))
    else:
        roles = config.get('series_roles', {})
        if not set(order).issubset(roles) or set(roles.values())-set(palette['roles']):
            raise ValueError(f'{palette_name} needs series_roles using {list(palette["roles"])}')
        colors = {key: palette['roles'][roles[key]] for key in order}
    result['palette'] = {key: {'fill': color, 'edge': color, 'label': '#20252c'}
                         for key, color in colors.items()}
    result['figure']['background'] = palette.get('background', result['figure']['background'])
    explicit = {key: value for key, value in config.items() if key != 'preset'}
    result = merge(result, explicit)
    if 'panels' not in config:
        result['panels'] = [{'id': key} for key in dict.fromkeys(row['panel'] for row in rows)]
    for panel in result['panels']:
        members = {row['series'] for row in rows if row['panel'] == panel['id']}
        legend = panel.setdefault('legend', {})
        if result['legend_defaults']['order'] is None:
            legend.setdefault('order', [key for key in order if key in members])
    result['resolved_preset'] = dict(style=style_name, layout=layout_name, palette=palette_name, font=font_name)
    return resolve_config(result, rows)


def opacity(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name} must be a finite number between 0 and 1')
    return value


def bar_colors(palette, style):
    """Separate face/edge RGBA; no artist-wide alpha that fades both together."""
    colors = []
    for part in ('fill', 'edge'):
        alpha = style[f'bar_{part}_alpha']
        if alpha is None:
            alpha = style['bar_alpha']
        if palette.get(f'{part}_alpha') is not None:
            alpha = palette[f'{part}_alpha']
        alpha = opacity(alpha, f'{part}_alpha')
        colors.append(matplotlib.colors.to_rgba(palette[part], alpha))
    return colors


def read_config(path):
    path = Path(path)
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    for icon in config.get('icons', []):
        if 'image' in icon:
            icon['image'] = str((path.parent/icon['image']).resolve())
    return config


def parse_override_value(path, raw):
    """Parse a --set value, falling back to a plain string.

    PowerShell strips double quotes from native arguments, so
    --set 'tokens.mode="raw"' arrives as tokens.mode=raw. Treating a bare value
    as a string keeps that command working. A value that still looks like a JSON
    object/array gets a targeted error instead of a raw JSONDecodeError.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if raw[:1] in ('{', '[', '"'):
            raise ValueError(
                f'{path}: value looks like JSON but could not be parsed: {raw!r}. '
                'On PowerShell, quotes are stripped from native arguments; '
                'use --set-file overrides.json for nested values.'
            ) from None
        return raw


def apply_override(config, assignment):
    """--set panel_defaults.value_size=9, --set tokens.mode=raw, or --set figure.svg_text=true."""
    path, sep, value = assignment.partition('=')
    if not sep:
        raise ValueError('Overrides must be dotted.path=VALUE')
    value = parse_override_value(path, value)
    keys = path.split('.')
    target = config
    for key in keys[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    key = int(keys[-1]) if isinstance(target, list) else keys[-1]
    if isinstance(target, dict) and key not in target:
        raise ValueError(f'Unknown parameter: {path}')
    target[key] = value


def check_override_keys(target, overrides, prefix=''):
    for key, value in overrides.items():
        if not isinstance(target, dict) or key not in target:
            raise ValueError(f'Unknown parameter in override file: {prefix}{key}')
        if isinstance(value, dict):
            check_override_keys(target[key], value, prefix + key + '.')


def apply_override_file(config, path):
    """Merge a JSON object of overrides; later --set values still win."""
    path = Path(path)
    overrides = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(overrides, dict):
        raise ValueError(f'Override file {path} must contain a JSON object')
    check_override_keys(config, overrides)
    return merge(config, overrides)


def load_data(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError('Input contains no rows')
    seen = set()
    for row in rows:
        for field in ('id', 'panel', 'group', 'series', 'value'):
            if not row.get(field):
                raise ValueError(f'Missing {field} in row {row}')
        if row['id'] in seen:
            raise ValueError(f'Duplicate row id: {row["id"]}')
        seen.add(row['id'])
        for key in ('value', 'low', 'high', 'x'):
            if row.get(key, '') != '':
                row[key] = float(row[key])
                if not math.isfinite(row[key]):
                    raise ValueError(f'Non-finite {key} in {row["id"]}')
            elif key in row:
                del row[key]
        if ('low' in row) != ('high' in row):
            raise ValueError('Supply both interval endpoints or neither')
        if 'low' in row and not row['low'] <= row['value'] <= row['high']:
            raise ValueError(f'Invalid interval in {row["id"]}')
    return rows


def font(config, role='light', size=9, font_dir=None):
    spec = config['fonts'][role]
    if font_dir and spec.get('file') and (Path(font_dir) / spec['file']).is_file():
        return fm.FontProperties(fname=str(Path(font_dir) / spec['file']), size=size)
    bundled = Path(__file__).parent / 'fonts' / (spec.get('file') or 'unused')
    if bundled.is_file():
        return fm.FontProperties(fname=str(bundled), size=size)
    families=spec['family'] if isinstance(spec['family'],list) else [spec['family']]
    for family in families:
        try:
            path=fm.findfont(fm.FontProperties(family=family,weight=spec['weight']),fallback_to_default=False)
        except ValueError:
            continue
        return fm.FontProperties(fname=path,size=size)
    raise ValueError(f'No available font for role {role}: {families}; configure fonts or --font-dir')


def positions(rows, style):
    """Explicit positions preserve measured layouts; otherwise arrange all groups."""
    mode = style['position_mode']
    if mode not in ('data', 'auto'):
        raise ValueError('position_mode must be data or auto')
    explicit = ['x' in row and mode == 'data' for row in rows]
    if any(explicit) and not all(explicit):
        raise ValueError('Explicit x positions must be supplied for every row in a panel')
    if all(explicit):
        return np.array([row['x'] for row in rows])
    groups = list(dict.fromkeys(row['group'] for row in rows))
    result, cursor = {}, 0.
    for group in groups:
        members = [row for row in rows if row['group'] == group]
        for row in members:
            result[row['id']] = cursor
            cursor += style['bar_width'] + style['series_gap']
        cursor += style['group_gap'] - style['series_gap']
    return np.array([result[row['id']] for row in rows])


def tint(color, amount=.84):
    rgb = np.array(matplotlib.colors.to_rgb(color))
    return tuple(rgb + (1-rgb)*amount)


def token_label(ax, x, tokens, style, config, palette, font_dir, shift_pt=0):
    if not tokens:
        return
    ts = style['tokens']
    parts = []; cursor = 0; max_height = 0
    for item in tokens:
        if isinstance(item, str): item = {'text': item}
        padding = item.get('padding_em', ts['padding_em'])
        height = item.get('height_em', ts['height_em'])*ts['size']
        baseline = item.get('baseline_em', ts['baseline_em'])*ts['size']
        y = item.get('y_offset_em', 0)*ts['size']
        runs = item.get('runs', [{'text': item.get('text',''), 'font': item.get('font','mono')}])
        texts = []; text_width = 0
        for run in runs:
            props = font(config, run.get('font','mono'), ts['size'], font_dir)
            width = TextToPath().get_text_width_height_descent(run['text'], props, False)[0]
            texts.append(Text(cursor+padding[0]*ts['size']+text_width, y+baseline,
                              run['text'], fontproperties=props, color=style['text_color']))
            text_width += width
        width = text_width + sum(padding)*ts['size']
        box = FancyBboxPatch((cursor,y),width,height,
            boxstyle=f'round,pad=0,rounding_size={ts["rounding"]*ts["size"]}',
            facecolor=palette.get('token_fill',tint(palette['fill'])) if ts['tint'] else ts['background'],
            edgecolor=palette.get('token_edge',palette['fill']) if ts['tint'] else ts['edge'],
            linewidth=ts['edge_width'])
        if ts['shadow']:
            box.set_path_effects([
                pe.SimplePatchShadow(offset=ts['shadow_offset'], alpha=ts['shadow_alpha']), pe.Normal()])
        parts.extend([box,*texts]); max_height=max(max_height,y+height)
        cursor += width + item.get('gap_after_pt',ts['gap'])
    pack = DrawingArea(cursor-item.get('gap_after_pt',ts['gap']),max_height,0,0)
    for part in parts: pack.add_artist(part)
    if style['orientation'] == 'vertical':
        point, coords, offset, align = (x, 0), ax.get_xaxis_transform(), (shift_pt, -ts['offset_pt']), (.5, 1)
    else:
        point, coords, offset, align = (0, x), ax.get_yaxis_transform(), (-ts['offset_pt'], 0), (1, .5)
    artist = AnnotationBbox(pack, point, xycoords=coords, xybox=offset, boxcoords='offset points',
                           frameon=False, box_alignment=align, pad=0, annotation_clip=False)
    ax.add_artist(artist)


def panel_rectangles(config):
    w, h = config['figure']['size_pt']; layout = config['layout']
    count = len(config['panels']); cols = min(count, layout['columns']); rows = math.ceil(count/cols)
    pw = (w-layout['left_pt']-layout['right_pt']-(cols-1)*layout['column_gap_pt'])/cols
    ph = (h-layout['top_pt']-layout['bottom_pt']-(rows-1)*layout['row_gap_pt'])/rows
    if min(pw, ph) <= 0:
        raise ValueError('Figure too small for this panel layout')
    for i, panel in enumerate(config['panels']):
        if 'rect_pt' in panel:
            yield panel['rect_pt']
        else:
            r, c = divmod(i, cols)
            yield [layout['left_pt']+c*(pw+layout['column_gap_pt']),
                   h-layout['top_pt']-(r+1)*ph-r*layout['row_gap_pt'], pw, ph]


def add_legend(ax, panel, rows, style, config, font_dir):
    spec=merge(config['legend_defaults'],panel.get('legend',{}))
    if not spec['show']:
        return
    present=list(dict.fromkeys(row['series'] for row in rows))
    order=spec['order'] if spec['order'] is not None else present
    if len(set(order))!=len(order) or set(order)!=set(present):
        raise ValueError('Legend order must include each plotted series exactly once')
    handles=[Patch(facecolor=bar_colors(config['palette'][key],style)[0],edgecolor=bar_colors(config['palette'][key],style)[1],
                   linewidth=style['bar_edge_width'],
                   hatch=config['palette'][key].get('hatch',style['hatch'])) for key in order]
    legend=ax.legend(handles,[spec['labels'].get(key,key) for key in order],
        prop=font(config,spec['font'],spec['size'],font_dir),loc=spec['loc'],
        bbox_to_anchor=spec['anchor'],ncol=spec['columns'],frameon=spec['frame'],
        facecolor=spec['facecolor'],edgecolor=spec['edgecolor'],framealpha=spec['frame_alpha'],
        fancybox=spec['rounded'],borderpad=spec['borderpad'],columnspacing=spec['columnspacing'],
        handlelength=spec['handlelength'],handleheight=spec['handleheight'],
        handletextpad=spec['handletextpad'],borderaxespad=spec['borderaxespad'])
    legend.get_frame().set_linewidth(spec['frame_width'])


def add_gain(fig, spec, artists, config, font_dir):
    """Anchor a cubic gain arrow to two current bar values; derive its label from data."""
    spec=merge(config['gain_defaults'],spec)
    before,after=artists[spec['from']],artists[spec['to']]
    if before['axis'] is not after['axis']:
        raise ValueError('Gain arrows must connect bars in one panel')
    if not before['vertical']:
        raise ValueError('Gain arrows currently require vertical panels')
    width,height=config['figure']['size_pt'];size=np.array([width,height])
    ax=before['axis']
    def point(item, anchor):
        bar=item['bar']
        positions={'left':bar.get_x(),'center':item['x'],'right':bar.get_x()+bar.get_width()}
        if anchor not in positions:
            raise ValueError('Gain anchors must be left, center or right')
        return fig.transFigure.inverted().transform(ax.transData.transform((positions[anchor],item['value'])))*size
    start=point(before,spec['tail_anchor'])+[spec['tail_dx_pt'],spec['tail_pad_pt']]
    end=point(after,spec['tip_anchor'])+[spec['tip_dx_pt'],spec['tip_pad_pt']]
    delta=end-start
    path=MplPath(np.array([start,start+delta*spec['control1'],start+delta*spec['control2'],end])/size,
                 [MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4])
    color=spec['color'] or config['palette'][after['series']][spec['palette_part']]
    arrow=FancyArrowPatch(path=path,transform=fig.transFigure,
        arrowstyle=f'-|>,head_length={spec["head_length_pt"]},head_width={spec["head_width_pt"]/2}',
        mutation_scale=1,linewidth=spec['linewidth'],color=color,alpha=opacity(spec['alpha'],'gain.alpha'),
        clip_on=spec['clip'],zorder=7)
    key=f'gain-{spec["from"]}-{spec["to"]}'
    arrow.set_gid(key+'-arrow');fig.add_artist(arrow)
    value=(after['value']-before['value'])*spec['label_scale']
    position=(start+delta*spec['label_position']+spec['label_offset_pt'])/size
    label=fig.text(*position,format(value,spec['label_format'])+spec['label_suffix'],ha='center',va='center',
                   color=color,alpha=opacity(spec['label_alpha'],'gain.label_alpha'),
                   fontproperties=font(config,spec['label_font'],spec['label_size'],font_dir))
    label.set_gid(key+'-label')


def build_figure(config, rows, font_dir=None):
    config = resolve_config(config, rows)
    ids = [p['id'] for p in config['panels']]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Panels need unique ids')
    if set(r['panel'] for r in rows) != set(ids):
        raise ValueError('CSV panels must match configured panels; no rows are silently dropped')
    w, h = config['figure']['size_pt']
    rc = {'pdf.fonttype': 42, 'svg.fonttype': 'none' if config['figure']['svg_text'] else 'path',
          'figure.facecolor': config['figure']['background'], 'axes.facecolor': config['figure']['background']}
    rc.update(config['rc'])
    with plt.rc_context(rc):
        fig = plt.figure(figsize=(w/72, h/72))
        artists, axes = {}, {}
        for panel, rect in zip(config['panels'], panel_rectangles(config)):
            style = merge(config['panel_defaults'], panel.get('style', {}))
            if style['orientation'] not in ('vertical','horizontal'):
                raise ValueError('orientation must be vertical or horizontal')
            vertical = style['orientation'] == 'vertical'
            if not vertical:
                row_ids={r['id'] for r in rows if r['panel']==panel['id']}
                if any(b['first'] in row_ids for b in config['bands']) or any(i.get('row') in row_ids for i in config['icons']):
                    raise ValueError('Group bands and row-bound icons currently require vertical panels')
            ax = fig.add_axes([rect[0]/w, rect[1]/h, rect[2]/w, rect[3]/h])
            axes[panel['id']] = ax
            rr = [r for r in rows if r['panel'] == panel['id']]
            xx = positions(rr, style)
            limits = style['limits']
            if limits[0] >= limits[1] or not limits[0] <= style['baseline'] <= limits[1]:
                raise ValueError('Invalid numeric limits or baseline')
            if any(r['value'] < limits[0] or r['value'] > limits[1] for r in rr):
                raise ValueError(f'Numeric limits clip bar heights in {panel["id"]}; expand limits explicitly')
            if not style['allow_interval_clipping'] and any(r.get('low',r['value']) < limits[0] or r.get('high',r['value']) > limits[1] for r in rr):
                raise ValueError(f'Numeric limits clip data in {panel["id"]}; expand limits explicitly')
            catlim = panel.get('category_limits', [xx.min()-style['bar_width']/2-style['category_margin'],
                                                  xx.max()+style['bar_width']/2+style['category_margin']])
            if vertical:
                ax.set(xlim=catlim, ylim=limits, yticks=style['ticks'], xticks=xx)
                ax.set_yticklabels([format(v,style['tick_format']) for v in style['ticks']])
            else:
                ax.set(ylim=catlim, xlim=limits, xticks=style['ticks'], yticks=xx)
                ax.set_xticklabels([format(v,style['tick_format']) for v in style['ticks']])
            for side in ('left','bottom','top','right'):
                ax.spines[side].set_visible(side in style['spines'])
                ax.spines[side].set_color(style['axis_color']); ax.spines[side].set_linewidth(style['axis_width'])
            ax.spines['bottom' if vertical else 'left'].set_linewidth(style['baseline_width'])
            ax.tick_params(length=style['tick_length'], width=style['tick_width'], pad=style['tick_pad'],
                           color=style['tick_color'], labelcolor=style['text_color'])
            category_axis, value_axis = ('x','y') if vertical else ('y','x')
            ax.tick_params(axis=value_axis, labelleft=style['show_value_ticks'] if vertical else False,
                           labelbottom=style['show_value_ticks'] if not vertical else False)
            if style['value_tick_length'] is not None:
                ax.tick_params(axis=value_axis,length=style['value_tick_length'])
            ax.tick_params(axis=category_axis, length=style['tick_length'] if style['show_category_ticks'] else 0,
                           pad=style['category_pad'], labelsize=style['category_size'])
            mode=style['tokens']['mode']
            if mode not in ('raw','readable'):
                raise ValueError('tokens.mode must be readable or raw')
            tokens=panel.get('readable_tokens',panel.get('tokens',{})) if mode=='readable' else panel.get('tokens',{})
            if style['category_mode']=='group':
                groups=list(dict.fromkeys(r['group'] for r in rr))
                ticks=[float(np.mean([x for x,r in zip(xx,rr) if r['group']==g])) for g in groups]
                (ax.set_xticks if vertical else ax.set_yticks)(ticks)
                labels=[panel.get('group_labels',{}).get(g,g) if style['show_categories'] else '' for g in groups]
            elif style['category_mode']=='bar':
                labels=[r.get('label',r['series']) if style['show_categories'] and not tokens.get(r['id']) else '' for r in rr]
            else:
                raise ValueError('category_mode must be bar or group')
            (ax.set_xticklabels if vertical else ax.set_yticklabels)(labels, rotation=style['category_rotation'])
            for label in (ax.get_yticklabels() if vertical else ax.get_xticklabels()):
                label.set_fontproperties(font(config,style['tick_font'],style['tick_size'],font_dir))
                label.set_alpha(opacity(style['text_alpha'],'text_alpha'))
            for label in (ax.get_xticklabels() if vertical else ax.get_yticklabels()):
                label.set_fontproperties(font(config,style['category_font'],style['category_size'],font_dir))
                label.set_alpha(opacity(style['text_alpha'],'text_alpha'))
            if style['invert_categories']:
                (ax.invert_xaxis if vertical else ax.invert_yaxis)()
            if style['ylabel']:
                setter = ax.set_ylabel if vertical else ax.set_xlabel
                setter(style['ylabel'], labelpad=style['label_pad'], color=style['text_color'],
                       alpha=opacity(style['text_alpha'],'text_alpha'),
                       fontproperties=font(config,style['label_font'],style['label_size'],font_dir))
            grid = style['grid']
            opacity(grid['alpha'], 'grid.alpha')
            if grid['kind'] == 'dots':
                cat_extent = rect[2] if vertical else rect[3]
                if grid['spacing_pt'] <= 0 or grid['value_step'] <= 0:
                    raise ValueError('Grid spacing must be positive')
                point_count = (cat_extent/grid['spacing_pt']+1)*((min(grid['value_stop'],limits[1])-limits[0])/grid['value_step']+1)
                if point_count > grid['max_points']:
                    raise ValueError('Grid is too dense; increase spacing or explicitly raise grid.max_points')
                step = grid['spacing_pt'] / cat_extent * (catlim[1]-catlim[0])
                gx = np.arange(catlim[0], catlim[1]+step*.001, step)
                gy = np.arange(limits[0], min(grid['value_stop'],limits[1])+grid['value_step']*.001,grid['value_step'])
                mx,my = np.meshgrid(gx,gy)
                ax.scatter(mx if vertical else my, my if vertical else mx, s=grid['size'],
                           color=grid['color'], alpha=grid['alpha'], edgecolors='none', zorder=0, clip_on=True)
            elif grid['kind'] == 'lines':
                linestyle=tuple(grid['linestyle']) if isinstance(grid['linestyle'],list) else grid['linestyle']
                ax.set_axisbelow(True); ax.grid(axis=value_axis,color=grid['color'],alpha=grid['alpha'],
                                               linewidth=grid['linewidth'],linestyle=linestyle)
            elif grid['kind'] != 'none':
                raise ValueError('grid.kind must be dots, lines, or none')
            for x, row in zip(xx, rr):
                palette = config['palette'][row['series']]
                fill, edge = bar_colors(palette, style)
                common = dict(color=fill, edgecolor=edge, linewidth=style['bar_edge_width'],
                              hatch=palette.get('hatch',style['hatch']),zorder=2)
                if vertical:
                    bar = ax.bar(x,row['value']-style['baseline'],width=style['bar_width'],bottom=style['baseline'],**common)[0]
                else:
                    bar = ax.barh(x,row['value']-style['baseline'],height=style['bar_width'],left=style['baseline'],**common)[0]
                error=None
                if 'low' in row:
                    error_values = [[row['value']-row['low']],[row['high']-row['value']]]
                    error = ax.errorbar(x if vertical else row['value'],row['value'] if vertical else x,
                                       **({'yerr':error_values} if vertical else {'xerr':error_values}),
                                       fmt='none',ecolor=style['error_color'],elinewidth=style['error_width'],
                                       capsize=style['error_cap'],capthick=style['error_width'],
                                       alpha=opacity(style['error_alpha'],'error_alpha'),zorder=4)
                label = None
                if style['value_labels']:
                    anchor = row.get('high',row['value']) if style['value_anchor']=='high' else row['value']
                    label=ax.annotate(format(row['value'],style['value_format']),
                        (x,anchor) if vertical else (anchor,x),
                        xytext=(0,style['value_pad']) if vertical else (style['value_pad'],0),
                        textcoords='offset points',ha='center' if vertical else 'left',
                        va='baseline' if vertical else 'center',
                        color=style['value_color'] or palette.get('label',palette['edge']),
                        alpha=opacity(style['value_alpha'] if palette.get('label_alpha') is None else palette['label_alpha'],'value_alpha'),
                        bbox={'boxstyle':f'square,pad={style["value_background_pad"]}',
                              'facecolor':config['figure']['background'],'edgecolor':'none'} if style['value_background'] else None,
                        fontproperties=font(config,style['value_font'],style['value_size'],font_dir),annotation_clip=False)
                if row['id'] in tokens:
                    token_label(ax,x,tokens[row['id']],style,config,palette,font_dir,
                                panel.get('token_shift_pt',{}).get(row['id'],0) if mode=='raw' else 0)
                artists[row['id']] = {'bar':bar,'error':error,'label':label,'x':float(x),'axis':ax,
                                      'value':row['value'],'series':row['series'],'vertical':vertical}
            add_legend(ax,panel,rr,style,config,font_dir)
        for spec in config['gains']:
            add_gain(fig,spec,artists,config,font_dir)
        for a in config['annotations']:
            color = a.get('color','#111111')
            if a.get('palette'): color=config['palette'][a['palette']][a.get('palette_part','edge')]
            props=dict(ha=a.get('ha','left'),va=a.get('va','baseline'),rotation=a.get('rotation',0),rotation_mode='anchor',color=color,
                       linespacing=a.get('linespacing',1.2),alpha=opacity(a.get('alpha',1),'annotation.alpha'),
                       fontproperties=font(config,a.get('font','light'),a['size'],font_dir))
            if a.get('box'):props['bbox']=a['box']
            fig.text(a['position_pt'][0]/w,a['position_pt'][1]/h,a['text'],**props)
        for band in config['bands']:
            first,last=artists[band['first']],artists[band['last']]
            ax=first['axis']
            if ax is not last['axis']: raise ValueError('A group band must lie in one panel')
            y=band['offset_pt']
            p0=fig.transFigure.inverted().transform(ax.transData.transform((first['x'],0)))
            p1=fig.transFigure.inverted().transform(ax.transData.transform((last['x'],0)))
            edge=config['palette'][band['palette']]['edge'] if band.get('palette') else '#111111'
            l=p0[0]-band['extend_pt']/w;r=p1[0]+band['extend_pt']/w;baseline=p0[1]-y/h
            fig.add_artist(plt.Line2D([l,r],[baseline,baseline],transform=fig.transFigure,color=edge,lw=band.get('width',.6)))
            fig.text((l+r)/2,baseline-band['text_offset_pt']/h,band['text'],ha='center',va='baseline',color=edge,
                     fontproperties=font(config,'regular',band['size'],font_dir))
        for icon in config['icons']:
            if 'image' in icon:
                item=artists[icon['row']];ax=item['axis'];bar=item['bar']
                center_y=bar.get_y()+bar.get_height()*icon['height_fraction']
                pw=ax.get_position().width*w;ph=ax.get_position().height*h
                iw=icon['width_pt']/pw*(ax.get_xlim()[1]-ax.get_xlim()[0])
                ih=icon['height_pt']/ph*(ax.get_ylim()[1]-ax.get_ylim()[0])
                ax.imshow(plt.imread(icon['image']),extent=(item['x']-iw/2,item['x']+iw/2,center_y-ih/2,center_y+ih/2),
                          interpolation=icon.get('interpolation','none'),aspect='auto',zorder=5)
                continue
            for shape in icon['paths']:
                vertices=[(x/w,y/h) for x,y in shape['vertices']]
                fig.add_artist(PathPatch(MplPath(vertices,shape['codes']),transform=fig.transFigure,
                    facecolor=shape.get('fill','none'),edgecolor=shape.get('stroke','none'),lw=shape.get('width',0),zorder=6))
        fig.canvas.draw()
    return fig, artists


def export_figure(fig, config, output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'pdf.fonttype':42,'svg.fonttype':'none' if config['figure']['svg_text'] else 'path'}):
        for ext in config['figure']['formats']:
            if ext not in ('png','pdf','svg'): raise ValueError(f'Unsupported export {ext}')
            fig.savefig(output.with_suffix('.'+ext),dpi=config['figure']['dpi'],facecolor=config['figure']['background'])


def render(config, rows, output, font_dir=None):
    config=resolve_config(config,rows)
    fig,artists=build_figure(config,rows,font_dir)
    export_figure(fig,config,output)
    plt.close(fig)
    return len(artists)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--data',type=Path,help='Replace CSV; otherwise resolve config.data relative to config file')
    parser.add_argument('--output',type=Path,help='Output stem; defaults to figure next to config')
    parser.add_argument('--font-dir',type=Path,help='Optional directory with locally licensed font files')
    parser.add_argument('--set',action='append',default=[],metavar='PATH=VALUE',help='Override one parameter; bare values are strings, JSON types are parsed')
    parser.add_argument('--set-file',action='append',default=[],type=Path,metavar='JSON',help='Merge a JSON object of overrides; use for nested values and on PowerShell')
    parser.add_argument('--defaults',action='store_true',help='Print complete default parameter groups')
    parser.add_argument('--list-presets',action='store_true',help='List styles, layouts, palettes and font profiles')
    for key in ('style','layout','palette','font'):
        parser.add_argument('--'+key,help=f'Select a {key} preset; explicit config fields still win')
    parser.add_argument('--resolved-config',type=Path,help='Write the complete resolved configuration for fine adjustments')
    args=parser.parse_args()
    if args.defaults: print(json.dumps(DEFAULTS,indent=2));return
    if args.list_presets:
        print(json.dumps({section:{key:value['description'] for key,value in choices.items()}
                          for section,choices in preset_catalog().items() if section in ('styles','layouts','palettes','fonts')},
                         ensure_ascii=False,indent=2));return
    if args.config is None and args.data is None: parser.error('Supply --config or --data')
    config=read_config(args.config) if args.config else {'preset':{}}
    for key in ('style','layout','palette','font'):
        if getattr(args,key) is not None: config.setdefault('preset',{})[key]=getattr(args,key)
    if args.data is None and 'data' not in config: parser.error('Configuration needs data or --data')
    data=args.data or args.config.parent/config['data']
    rows=load_data(data)
    config=resolve_config(config,rows)
    for path in args.set_file: config=apply_override_file(config,path)
    for assignment in args.set: apply_override(config,assignment)
    if args.resolved_config:
        args.resolved_config.parent.mkdir(parents=True,exist_ok=True)
        snapshot=merge(config,{'data':str(data.resolve())})
        args.resolved_config.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    output=args.output or (args.config.parent/'figure' if args.config else Path('output/figure'))
    count=render(config,rows,output,args.font_dir)
    missing=[name for name,s in config['fonts'].items() if s.get('file') and not
             ((args.font_dir and s.get('file') and (args.font_dir/s['file']).is_file()) or
              (s.get('file') and (Path(__file__).parent/'fonts'/s['file']).is_file()))]
    print(json.dumps({'rendered_bars':count,'font_fallback_roles':missing,'output':str(output)}))


if __name__=='__main__':
    main()
