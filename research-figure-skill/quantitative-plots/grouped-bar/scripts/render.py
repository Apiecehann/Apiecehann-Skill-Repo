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
import warnings
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
from matplotlib.transforms import Bbox
from matplotlib.patches import PathPatch, FancyBboxPatch, FancyArrowPatch, Patch, Rectangle
import numpy as np

DEFAULTS = {
    'figure': {'size_pt': [540, 180], 'background': 'white', 'dpi': 300,
               'formats': ['png', 'pdf', 'svg'], 'svg_text': True},
    'fonts': {'light': {'family': ['Liberation Sans','Arial','DejaVu Sans'], 'weight': 'normal', 'file': 'Graphik-Light.ttf'},
              'regular': {'family': ['Liberation Sans','Arial','DejaVu Sans'], 'weight': 'normal', 'file': 'Graphik-Regular.ttf'},
              'mono': {'family': 'DejaVu Sans Mono', 'weight': 'normal', 'file': 'B612Mono-Regular.ttf'}},
    'palette': {'base': {'fill': '#a1a1a1', 'edge': '#525252', 'label': '#404040'},
                'cue': {'fill': '#fabc00', 'edge': '#da7700', 'label': '#b45300'},
                'rl': {'fill': '#56a2ff', 'edge': '#155dfc', 'label': '#1447e6'},
                'edit': {'fill': '#ff6568', 'edge': '#e40016', 'label': '#bf000f'},
                'answer': {'fill': '#a686ff', 'edge': '#7f22fe', 'label': '#7008e7'}},
    'panel_defaults': {
        'orientation': 'vertical', 'limits': 'auto', 'ticks': 'auto',
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
        'reference_lines': [],
        'increment': {'field': None, 'hatch': '////', 'gap_pt': 1.5, 'pad_pt': 1.5,
                      'label_format': '{total}', 'delta_format': '+{delta:g}',
                      'reference_line': False, 'hatch_color': None},
        'capacity': {'field': None, 'linestyle': '--', 'edge_width': .7,
                     'alpha': .45, 'label_format': '{value}/{capacity}', 'show_percent': True},
        'grid': {'kind': 'dots', 'spacing_pt': 10.5, 'value_step': 'auto',
                 'value_stop': 'auto', 'axis': 'value',
                 'size': .75, 'color': '#bdbdbd', 'alpha': 1, 'max_points': 50000,
                 'linewidth': .5, 'linestyle': '-'},
        'tokens': {'mode': 'readable', 'size': 6.3, 'gap': 2.6, 'padding_em': [.16, .16],
                   'height_em': 1.333333, 'baseline_em': .405, 'rounding': .194444,
                   'edge_width': .4, 'background': '#f5f5f5', 'edge': '#262626',
                   'shadow': True, 'shadow_offset': [.35, -.55], 'shadow_alpha': .28,
                   'offset_pt': 6, 'tint': False},
    },
    'legend_defaults': {'show': False, 'order': None, 'labels': {}, 'font': 'regular', 'size': 10,
                        'loc': 'upper center', 'anchor': [.5,1.2], 'columns': 'auto', 'frame': True,
                        'facecolor': 'white', 'edgecolor': '#cccccc', 'frame_alpha': 1,
                        'frame_width': .8, 'rounded': True, 'borderpad': .4,
                        'columnspacing': 2, 'handlelength': 2, 'handleheight': .7,
                        'handletextpad': .8, 'borderaxespad': .5},
    'gain_defaults': {'auto_layout': True, 'clearance_pt': 5,
                     'label_collision_pad_pt': 2, 'label_leader_pt': 8, 'color': None, 'palette_part': 'edge', 'linewidth': 2.5,
                     'alpha': 1, 'label_alpha': 1, 'arrow_style': 'route',
                     'head_length_pt': 7, 'head_width_pt': 6, 'tail_pad_pt': 5, 'tip_pad_pt': 9,
                     'tail_dx_pt': -12, 'tip_dx_pt': -16,
                     'tail_anchor': 'center', 'tip_anchor': 'center',
                     'control1': [.55,0], 'control2': [.9,.55],
                     'label_position': [.5,.48], 'label_offset_pt': [-8,0],
                     'label_size': 15, 'label_font': 'regular', 'label_format': '+.1f',
                     'label_scale': 1, 'label_suffix': '', 'label_side': 'above', 'clip': False},
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


def palette_colors(name, order, roles):
    """Resolve a palette preset to {series: hex} without mutating config."""
    palettes = preset_catalog()['palettes']
    if name not in palettes:
        raise ValueError(f'Unknown palettes preset {name!r}; choose from {list(palettes)}')
    palette = palettes[name]
    if palette['kind'] == 'categorical':
        if len(order) > len(palette['colors']):
            raise ValueError(f'{name} supports at most {len(palette["colors"])} series; choose another palette')
        return dict(zip(order, palette['colors'])), palette
    if not set(order).issubset(roles) or set(roles.values()) - set(palette['roles']):
        raise ValueError(f'{name} needs series_roles using {list(palette["roles"])}')
    return {key: palette['roles'][roles[key]] for key in order}, palette


def apply_palette_selection(config, rows, name):
    """Apply --palette after resolution, so it also wins on frozen replicas."""
    present = list(dict.fromkeys(row['series'] for row in rows))
    order = config.get('series_order', present)
    if not order or len(set(order)) != len(order) or not set(present).issubset(order):
        raise ValueError('series_order must be unique and include every plotted series')
    colors, palette = palette_colors(name, order, config.get('series_roles', {}))
    for key, color in colors.items():
        previous = dict(config['palette'].get(key, {}))
        for stale in ('token_fill', 'token_edge'):
            previous.pop(stale, None)
        config['palette'][key] = {**previous, 'fill': color, 'edge': color, 'label': '#20252c'}
    config['figure']['background'] = palette.get('background', config['figure']['background'])
    config.setdefault('resolved_preset', {})['palette'] = name


def apply_font_selection(config, name):
    fonts = preset_catalog()['fonts']
    if name not in fonts:
        raise ValueError(f'Unknown fonts preset {name!r}; choose from {list(fonts)}')
    config['fonts'] = copy.deepcopy(fonts[name]['roles'])
    config.setdefault('resolved_preset', {})['font'] = name


def resolve_config(config, rows):
    """Compose defaults < style < layout < size < palette/font < explicit configuration.

    Presets never set numeric limits, ticks, baselines or interval definitions.
    The six measured reference configurations still use the original path.
    """
    if 'preset' not in config:
        result = merge(DEFAULTS, config)
        if config.get('frozen_config') and 'auto_layout' not in config.get('gain_defaults', {}):
            result['gain_defaults']['auto_layout'] = False
        for entry in result['palette'].values():
            for key in ('fill_alpha','edge_alpha','label_alpha'):
                entry.setdefault(key, None)
        return result
    catalog = preset_catalog()
    selection = config['preset']
    if not isinstance(selection, dict) or set(selection)-{'style','layout','size','palette','font'}:
        raise ValueError('preset accepts style, layout, size, palette and optional font')
    style_name = selection.get('style', 'paper-clean')
    layout_name = selection.get('layout', 'grouped')
    def pick(section, name):
        if name not in catalog[section]:
            raise ValueError(f'Unknown {section} preset {name!r}; choose from {list(catalog[section])}')
        return catalog[section][name]
    style = pick('styles', style_name)
    layout = pick('layouts', layout_name)
    size_name = selection.get('size')
    size = pick('sizes', size_name) if size_name else None
    palette_name = selection.get('palette', layout.get('palette', style['palette']))
    palette = pick('palettes', palette_name)
    font_name = selection.get('font', style['font'])
    typography = pick('fonts', font_name)
    result = merge(merge(DEFAULTS, style['config']), layout['config'])
    if size:
        result = merge(result, size['config'])
    result['fonts'] = copy.deepcopy(typography['roles'])
    present = list(dict.fromkeys(row['series'] for row in rows))
    order = config.get('series_order', present)
    if not order or len(set(order)) != len(order) or not set(present).issubset(order):
        raise ValueError('series_order must be unique and include every plotted series')
    colors, palette = palette_colors(palette_name, order, config.get('series_roles', {}))
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
    result['resolved_preset'] = dict(style=style_name, layout=layout_name, size=size_name,
                                     palette=palette_name, font=font_name)
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
        for key in ('value', 'low', 'high', 'x', 'capacity', 'base'):
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
    validate_increment(rows, -math.inf)
    validate_capacity(rows, -math.inf)
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


def nice_step(span, target=5):
    """A 1/2/2.5/5 x 10^n step that gives roughly `target` intervals."""
    if span <= 0:
        return 1.0
    raw = span / target
    exponent = math.floor(math.log10(raw))
    base = 10 ** exponent
    for factor in (1, 2, 2.5, 5, 10):
        if factor * base >= raw - 1e-12:
            return factor * base
    return 10 * base


def nice_ticks(limits, target=5):
    lower, upper = limits
    step = nice_step(upper - lower, target)
    value = math.ceil(lower / step - 1e-9) * step
    ticks = []
    while value <= upper + 1e-9:
        ticks.append(round(value, 10))
        value += step
    return ticks


def validate_capacity(rows, baseline, field=None):
    """Normalize an optional capacity field and reject ambiguous panel semantics."""
    if field is not None:
        if not isinstance(field, str) or not field:
            raise ValueError('capacity.field must be a column name or null')
        normalized = []
        for row in rows:
            if row.get(field, '') == '':
                raise ValueError(f'Missing capacity field {field!r} in {row["id"]}')
            try:
                value = float(row[field])
            except (TypeError, ValueError):
                raise ValueError(f'Invalid capacity in {row["id"]}: expected a finite number') from None
            normalized.append({**row, 'capacity': value})
        rows = normalized
    for panel in dict.fromkeys(r['panel'] for r in rows):
        members = [r for r in rows if r['panel'] == panel]
        present = ['capacity' in r for r in members]
        if any(present) and not all(present):
            raise ValueError(f'Panel {panel}: all rows must supply capacity or none')
        for row in members:
            if 'capacity' not in row:
                continue
            if type(row['capacity']) not in (int, float) or not math.isfinite(row['capacity']):
                raise ValueError(f'Non-finite or invalid capacity in {row["id"]}')
            if 'low' in row or 'high' in row:
                raise ValueError(f'Interval + capacity is not supported in {row["id"]}')
            if not row['capacity'] >= row['value'] >= baseline:
                raise ValueError(f'Row {row["id"]}: require capacity >= value >= baseline ({baseline})')
    return rows


def validate_increment(rows, baseline=0, orientation='vertical', field=None):
    """Validate base data even when drawing is disabled; normalize custom fields."""
    if field is not None:
        if not isinstance(field, str) or not field:
            raise ValueError('increment.field must be a column name or null')
        normalized = []
        for row in rows:
            if row.get(field, '') == '':
                raise ValueError(f'Missing base field {field!r} in {row["id"]}')
            try:
                base = float(row[field])
            except (TypeError, ValueError):
                raise ValueError(f'Invalid base in {row["id"]}: expected a finite number') from None
            normalized.append({**row, 'base': base})
        rows = normalized
    for panel in dict.fromkeys(row['panel'] for row in rows):
        members = [r for r in rows if r['panel'] == panel]
        present = ['base' in r for r in members]
        if any(present) and not all(present):
            raise ValueError(f'Panel {panel}: all rows must supply base or none')
        for row in members:
            if 'base' not in row:
                continue
            if orientation != 'vertical':
                raise ValueError('Base-plus-increment bars require vertical layout; horizontal is not supported')
            if any(key in row for key in ('low', 'high', 'capacity')):
                raise ValueError(f'Row {row["id"]}: base cannot be combined with intervals or capacity')
            if any(type(row[k]) not in (int, float) or not math.isfinite(row[k]) for k in ('base', 'value')):
                raise ValueError(f'Row {row["id"]}: base and value must be finite')
            if not 0 <= row['base'] <= row['value']:
                raise ValueError(f'Row {row["id"]}: require 0 <= base <= value')
            if baseline > row['base']:
                raise ValueError(f'Row {row["id"]}: baseline must not exceed base')
    return rows


def increment_text(row, template):
    try:
        if template == '{total}':
            return f'{row["value"]:g}'
        return template.format(total=row['value'], base=row['base'], delta=row['value']-row['base'])
    except (ValueError, KeyError, AttributeError, IndexError, TypeError) as exc:
        raise ValueError(f'Invalid increment label format {template!r}; use total, base or delta: {exc}') from None


def draw_increment(ax, x, row, style, config, palette):
    """Draw two segments; expose an invisible total-extent bar for legacy consumers."""
    spec = style['increment']
    gap = spec['gap_pt']
    if type(gap) not in (int, float) or not math.isfinite(gap) or gap < 0:
        raise ValueError('increment.gap_pt must be a finite nonnegative number')
    fill, edge = bar_colors(palette, style)
    hatch_edge = matplotlib.colors.to_rgba(spec['hatch_color'], edge[3]) if spec['hatch_color'] else edge
    base_bar = ax.bar(x, row['base']-style['baseline'], width=style['bar_width'], bottom=style['baseline'],
        facecolor=(*tint(palette['fill'], .7), fill[3]), edgecolor=hatch_edge,
        linewidth=max(.5, style['bar_edge_width']), hatch=spec['hatch'], zorder=2)[0]
    increment_bar = ax.bar(x, row['value']-row['base'], width=style['bar_width'], bottom=row['base'],
        facecolor=fill, edgecolor='none', linewidth=0, hatch=None, zorder=2)[0]
    # Never draw an extra full bar over the two actual segments.
    total_bar = Rectangle((x-style['bar_width']/2, style['baseline']), style['bar_width'],
                          row['value']-style['baseline'], visible=False)
    ax.add_patch(total_bar)
    separator = reference = None
    if gap and style['baseline'] < row['base'] < row['value']:
        separator, = ax.plot([x-style['bar_width']/2, x+style['bar_width']/2], [row['base']]*2,
                             color=config['figure']['background'], linewidth=gap,
                             solid_capstyle='butt', zorder=3)
    if spec['reference_line']:
        reference = ax.axhline(row['base'], color=palette['edge'], linewidth=.5, linestyle='--', zorder=1)
    base_bar.set_gid('increment-'+row['id']+'-base')
    increment_bar.set_gid('increment-'+row['id']+'-increment')
    return dict(bar=total_bar, base_bar=base_bar, increment_bar=increment_bar,
                increment_separator=separator, increment_reference=reference)


def add_increment_label(fig, ax, x, row, item, style, config, palette, font_dir):
    """Use measured segment bounds; a small increment gets an external leader label."""
    text = increment_text(row, style['increment']['delta_format'])
    middle = row['base'] + (row['value']-row['base'])/2
    label = ax.text(x, middle, text, ha='center', va='center', zorder=5,
                    color=style['value_color'] or palette.get('label', palette['edge']),
                    fontproperties=font(config, style['value_font'], style['value_size'], font_dir))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    box = label.get_window_extent(renderer)
    segment = item['increment_bar'].get_window_extent(renderer)
    pad = fig.dpi/72*style['increment'].get('pad_pt', 1.5)
    gap = fig.dpi/72*style['increment']['gap_pt']/2
    fits = (box.width + 2*pad <= segment.width and box.height + 2*pad + gap <= segment.height)
    leader = None
    if not fits:
        total = item['label'].get_window_extent(renderer)
        # Place above the total text, not over the nearly zero-height segment.
        point = ax.transData.transform((x, row['value']))
        point[1] = max(point[1], total.y1) + pad + box.height/2
        left = x + style['bar_width']/2
        label.set_position(ax.transData.inverted().transform(point))
        anchor = ax.transData.transform((left, middle))
        end = np.array([point[0] + box.width/2 + pad, point[1]])
        elbow = np.array([max(anchor[0], end[0]) + pad, anchor[1]])
        vertices = ax.transData.inverted().transform([anchor, elbow, [elbow[0], end[1]], end])
        leader, = ax.plot(vertices[:, 0], vertices[:, 1], color=palette['edge'], linewidth=.5,
                          clip_on=False, zorder=4)
        leader.set_gid('increment-'+row['id']+'-leader')
    label.set_gid('increment-'+row['id']+'-delta-label')
    item.update(increment_label=label, increment_leader=leader, increment_label_inside=fits)


def capacity_text(row, spec):
    value, capacity = row['value'], row['capacity']
    percent = 100 * value / capacity if capacity else None
    template = spec['label_format']
    try:
        if template == '{value}/{capacity}':
            text = f'{value:g} / {capacity:g}'
        else:
            text = template.format(value=value, capacity=capacity, percent=percent)
    except (ValueError, KeyError, AttributeError, IndexError, TypeError) as exc:
        raise ValueError(f'Invalid capacity.label_format {template!r}; use value, capacity or percent: {exc}') from None
    if spec['show_percent']:
        text += f' ({percent:.0f}%)' if percent is not None else ' (n/a)'
    return text


def auto_axis(rows, baseline):
    """Derive limits and ticks from data, including intervals and capacity; never clips silently."""
    highs = [max(row.get('high', row['value']), row.get('capacity', row['value'])) for row in rows]
    lows = [row.get('low', row['value']) for row in rows]
    top = max(highs + [baseline])
    bottom = min(lows + [baseline])
    if not math.isfinite(top) or not math.isfinite(bottom):
        raise ValueError('Non-finite data cannot define an axis')
    span = top - bottom
    if span <= 0:
        span = max(abs(top), 1.0) * 0.1
    # Keep the headroom tight: 85% should end at 90%, not 100%.
    step = nice_step(span * 1.02, target=12)
    lower = math.floor((bottom * 0.98) / step) * step
    upper = math.ceil((top * 1.02) / step) * step
    if baseline == 0 and bottom >= 0:
        lower = 0.0
    if top <= 0:
        upper = 0.0
    if upper <= lower:
        upper = lower + step
    ticks = [round(lower + i * step, 10) for i in range(int(round((upper - lower) / step)) + 1)]
    return [round(lower, 10), round(upper, 10)], ticks


def panel_axis(rows, style, height_pt, config):
    """Resolve the data axis, reserving physical room only for automatic gains."""
    limits, ticks = style['limits'], style['ticks']
    if limits == 'auto':
        limits, auto_ticks = auto_axis(rows, style['baseline'])
        ids = {r['id'] for r in rows}
        gains = [merge(config['gain_defaults'], g) for g in config['gains']
                 if g['from'] in ids and g['to'] in ids]
        gains = [g for g in gains if g['auto_layout']]
        if gains:
            reserve = max(g['clearance_pt']*2 + g['label_collision_pad_pt']*3 +
                          g['label_size']*1.3 + max(g['head_length_pt'], 8) + 6 for g in gains)
            if style['value_labels'] or style['increment']['field']:
                reserve += style['value_pad'] + style['value_size']*1.3
            if reserve >= height_pt*.8:
                raise ValueError('Panel too short for automatic delta annotations; increase figure height or use auto_layout=false')
            top = max(max(r.get('capacity', r['value']), r.get('high', r['value'])) for r in rows)
            upper = limits[0] + (top-limits[0])/(1-reserve/height_pt)
            step = nice_step(max(upper-limits[0], 1e-12), target=12)
            limits = [limits[0], max(limits[1], math.ceil(upper/step)*step)]
            auto_ticks = nice_ticks(limits)
        if ticks == 'auto':
            ticks = auto_ticks
    elif ticks == 'auto':
        ticks = nice_ticks(limits)
    return limits, ticks


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
    panels = config['panels']
    if panels and all('rect_pt' in panel for panel in panels):
        for panel in panels:
            yield panel['rect_pt']
        return
    count = len(panels); cols = min(count, layout['columns']); rows = math.ceil(count/cols)
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


def add_legend(fig, ax, panel, rows, style, config, font_dir):
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
    labels=[spec['labels'].get(key,key) for key in order]
    def make(columns):
        return ax.legend(handles,labels,
            prop=font(config,spec['font'],spec['size'],font_dir),loc=spec['loc'],
            bbox_to_anchor=spec['anchor'],ncol=columns,frameon=spec['frame'],
            facecolor=spec['facecolor'],edgecolor=spec['edgecolor'],framealpha=spec['frame_alpha'],
            fancybox=spec['rounded'],borderpad=spec['borderpad'],columnspacing=spec['columnspacing'],
            handlelength=spec['handlelength'],handleheight=spec['handleheight'],
            handletextpad=spec['handletextpad'],borderaxespad=spec['borderaxespad'])
    if spec['columns'] == 'auto':
        width_pt=config['figure']['size_pt'][0]
        center=(ax.get_position().x0+float(spec['anchor'][0])*ax.get_position().width)*width_pt
        available=max(2*min(center,width_pt-center)-4,10)
        for count in range(len(labels),0,-1):
            legend=make(count)
            fig.canvas.draw()
            width=legend.get_window_extent(fig.canvas.get_renderer()).width*72/fig.dpi
            if width <= available:
                break
            legend.remove()
        else:
            legend=make(1)
    else:
        legend=make(int(spec['columns']))
    legend.get_frame().set_linewidth(spec['frame_width'])
    fig.canvas.draw()
    bbox=legend.get_window_extent(fig.canvas.get_renderer())
    if bbox.x0 < 0 or bbox.y0 < 0 or bbox.x1 > fig.bbox.x1 or bbox.y1 > fig.bbox.y1:
        warnings.warn('Legend extends outside the figure; increase layout margins or reduce legend.size', UserWarning)


def point_bbox(artist, renderer, scale):
    box = artist.get_window_extent(renderer)
    return Bbox.from_extents(*(np.array(box.extents)*scale))


def padded(box, amount):
    return Bbox.from_extents(box.x0-amount, box.y0-amount, box.x1+amount, box.y1+amount)


def sample_cubic_path(path, count=96):
    """Sample each Bezier segment, including its ends, in the path's coordinates."""
    points = [path.vertices[0]]
    start = path.vertices[0]
    for i in range(1, len(path.vertices), 3):
        c1, c2, end = path.vertices[i:i+3]
        t = np.linspace(0, 1, count+1)[1:, None]
        points.extend((1-t)**3*start + 3*(1-t)**2*t*c1 + 3*(1-t)*t**2*c2 + t**3*end)
        start = end
    return np.asarray(points)


def points_hit_box(points, box):
    return bool(np.any((points[:, 0] >= box.x0) & (points[:, 0] <= box.x1) &
                       (points[:, 1] >= box.y0) & (points[:, 1] <= box.y1)))


def gain_route(start, end, ceiling, lift):
    """Three cubic segments: rise, traverse above intervening marks, then descend."""
    across = end[0]-start[0]
    first = np.array([start[0], ceiling])
    last = np.array([end[0], ceiling])
    vertices = [start, start+(first-start)/3, start+2*(first-start)/3, first,
                first+[across/3, lift], first+[2*across/3, lift], last,
                last+(end-last)/3, last+2*(end-last)/3, end]
    return MplPath(vertices, [MplPath.MOVETO]+[MplPath.CURVE4]*9)


def gain_route_arc(start, end, ceiling):
    """One smooth cubic arch; kept for compatibility with the first curved draft."""
    vertices = [start, [start[0], ceiling], [end[0], ceiling], end]
    return MplPath(vertices, [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])


def gain_route_curved(start, end, rise):
    """A rising cubic whose end tangent points up-right instead of hooking down."""
    dx, dy = end[0]-start[0], end[1]-start[1]
    sign = 1 if dy >= 0 else -1
    c1 = [start[0]+dx*.55, start[1]+sign*rise]
    c2 = [end[0]-dx*.18, end[1]-sign*rise]
    return MplPath([start, c1, c2, end],
                   [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])


def add_auto_gain(fig, spec, artists, config, font_dir):
    """Route above obstacles and place measured text inside the panel's free space."""
    before, after = artists[spec['from']], artists[spec['to']]
    ax = before['axis']
    for key in ('clearance_pt', 'label_collision_pad_pt', 'label_leader_pt'):
        if type(spec[key]) not in (int, float) or not math.isfinite(spec[key]) or spec[key] < 0:
            raise ValueError(f'gain.{key} must be a finite nonnegative number')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    scale = 72/fig.dpi
    width, height = config['figure']['size_pt']
    size = np.array([width, height])
    panel = point_bbox(ax, renderer, scale)
    margin = max(1.5, spec['label_collision_pad_pt'])
    inner = padded(panel, -margin)
    members = [item for item in artists.values() if item['axis'] is ax]
    bars = [point_bbox(item['bar'], renderer, scale) for item in members]
    texts = []
    for item in members:
        for key in ('label', 'capacity_label', 'increment_label'):
            text = item.get(key)
            if text is not None and text.get_visible():
                texts.append(point_bbox(text, renderer, scale))
        if item.get('capacity_bar') is not None:
            bars.append(point_bbox(item['capacity_bar'], renderer, scale))
    previous = [gain for item in members for gain in item.get('auto_gains', [])]
    texts += [point_bbox(g['label'], renderer, scale) for g in previous]
    clearance = max(spec['clearance_pt'], spec['head_width_pt']/2+1, 2)
    obstacles = [padded(b, 1+spec['linewidth']/2) for b in bars]
    obstacles += [padded(b, spec['label_collision_pad_pt']) for b in texts]
    def anchor(item, name):
        box = point_bbox(item['bar'], renderer, scale)
        xs = {'left': box.x0, 'center': (box.x0+box.x1)/2, 'right': box.x1}
        if name not in xs:
            raise ValueError('Gain anchors must be left, center or right')
        x, y = xs[name], box.y1+clearance
        # A value label may sit directly above this bar; start above that label too.
        for obstacle in obstacles:
            if obstacle.x0-clearance/2 <= x <= obstacle.x1+clearance/2:
                y = max(y, obstacle.y1+clearance)
        return np.array([x, y])
    start, end = anchor(before, spec['tail_anchor']), anchor(after, spec['tip_anchor'])
    if spec.get('arrow_style') == 'curved':
        # End above the bar top; otherwise the rising tip has to enter the bar to point up-right.
        start = start + np.array([0, 2])
        end = end + np.array([0, 4])
    left, right = sorted((start[0], end[0]))
    across, change = abs(end[0]-start[0]), end[1]-start[1]
    lift = min(3., across*.06)
    ceiling = max(start[1], end[1]) + max(3., min(across*.1, 8.), abs(change)*.08)
    for box in obstacles:
        if box.x0 <= right and box.x1 >= left:
            ceiling = max(ceiling, box.y1+clearance)
    style = spec.get('arrow_style', 'route')
    if style not in ('route', 'curved'):
        raise ValueError('gain.arrow_style must be route or curved')
    rise = max(4., abs(across)*.12, abs(change)*.25)
    for attempt in range(8):
        path = (gain_route_curved(start, end, rise) if style == 'curved'
                else gain_route(start, end, ceiling, lift))
        points = sample_cubic_path(path)
        bad = (np.any(points[:, 0] < inner.x0) or np.any(points[:, 0] > inner.x1) or
               np.any(points[:, 1] < inner.y0) or np.any(points[:, 1] > inner.y1) or
               any(points_hit_box(points, box) for box in obstacles))
        if not bad:
            break
        if style != 'curved' or attempt == 7:
            raise ValueError('No collision-free delta path inside panel; increase y_max or figure height')
        rise += 3

    color = spec['color'] or config['palette'][after['series']][spec['palette_part']]
    value = (after['value']-before['value'])*spec['label_scale']
    key = f'gain-{spec["from"]}-{spec["to"]}'
    label = fig.text(0, 0, format(value, spec['label_format'])+spec['label_suffix'],
                     ha='center', va='center', color=color,
                     alpha=opacity(spec['label_alpha'], 'gain.label_alpha'),
                     fontproperties=font(config, spec['label_font'], spec['label_size'], font_dir))
    label.set_gid(key+'-label')
    # Text.get_window_extent measures with the current renderer without another draw.
    measured = point_bbox(label, renderer, scale)
    half_w, half_h = measured.width/2, measured.height/2
    # Keep a group's label over its own slot, not over an adjacent group.
    region = [inner.x0, inner.x1]
    if before['group'] == after['group']:
        own = [b for b, item in zip(bars, members) if item['group'] == before['group']]
        other = [b for b, item in zip(bars, members) if item['group'] != before['group']]
        own_left, own_right = min(b.x0 for b in own), max(b.x1 for b in own)
        for box in other:
            if box.x1 <= own_left:
                region[0] = max(region[0], (box.x1+own_left)/2)
            if box.x0 >= own_right:
                region[1] = min(region[1], (box.x0+own_right)/2)
    lo, hi = region[0]+half_w+margin, region[1]-half_w-margin
    # A very wide label may use a free panel margin with a leader; never put it on bars.
    constrained = lo <= hi
    if not constrained:
        lo, hi = inner.x0+half_w, inner.x1-half_w
    if lo > hi:
        label.remove()
        raise ValueError('Delta label wider than panel; increase figure width or shorten label_format/label_suffix')
    outward = 1 if (end[1] >= start[1]) == (end[0] >= start[0]) else -1
    desired = (right+half_w+margin if outward > 0 else left-half_w-margin)
    xs = [desired, (left+right)/2, left-half_w-margin, right+half_w+margin, lo, hi]
    xs = list(dict.fromkeys(float(np.clip(x, lo, hi)) for x in xs))
    above = points[:, 1].max()+margin+half_h
    ys = [above + i*(2+half_h) for i in range(6)]
    ys += list(np.arange(inner.y1-half_h, inner.y0+half_h, -max(half_h, 2)))
    side = spec.get('label_side', 'above')
    if side not in ('above', 'left'):
        raise ValueError('gain.label_side must be above or left')
    shift = spec.get('label_shift_pt', [0, 0])
    if (not isinstance(shift, (list, tuple)) or len(shift) != 2 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in shift)):
        raise ValueError('gain.label_shift_pt must be two finite numbers')
    if side == 'left':
        ys = [max(start[1], end[1])+margin+half_h+shift[1]] + ys
        xs = [start[0]-half_w-margin+shift[0]] + xs
    all_paths = [points] + [g['points_pt'] for g in previous]
    position = None
    leader_points = None
    for y in ys:
        if not inner.y0+half_h <= y <= inner.y1-half_h:
            continue
        for x in xs:
            candidate = Bbox.from_extents(x-half_w, y-half_h, x+half_w, y+half_h)
            expanded = padded(candidate, margin)
            if any(expanded.overlaps(obstacle) for obstacle in obstacles):
                continue
            if any(points_hit_box(p, expanded) for p in all_paths):
                continue
            # Link displaced labels to the top of the route, avoiding bars and text.
            center = points[np.argmax(points[:, 1])]
            displacement = abs(x-(left+right)/2)
            leader = None
            if displacement > spec['label_leader_pt'] or not constrained or y < above:
                edge = np.array([np.clip(center[0], candidate.x0, candidate.x1),
                                 candidate.y0 if y >= center[1] else candidate.y1])
                leader = np.linspace(center, edge, 96)
                if any(points_hit_box(leader[1:-1], obstacle) for obstacle in obstacles):
                    continue
            position, leader_points = np.array([x, y]), leader
            break
        if position is not None:
            break
    if position is None:
        label.remove()
        raise ValueError('No free space for delta label; increase y_max/figure size or shorten its text')
    label.set_position(position/size)
    arrow = FancyArrowPatch(path=MplPath(path.vertices/size, path.codes), transform=fig.transFigure,
        arrowstyle=f'-|>,head_length={spec["head_length_pt"]},head_width={spec["head_width_pt"]/2}',
        mutation_scale=1, linewidth=spec['linewidth'], color=color,
        alpha=opacity(spec['alpha'], 'gain.alpha'), clip_on=False, zorder=7)
    arrow.set_gid(key+'-arrow')
    fig.add_artist(arrow)
    leader_artist = None
    if leader_points is not None and side != 'left':
        leader_artist = plt.Line2D(leader_points[:, 0]/width, leader_points[:, 1]/height,
                                  transform=fig.transFigure, color=color, linewidth=.5, zorder=6)
        leader_artist.set_gid(key+'-leader')
        fig.add_artist(leader_artist)
    before.setdefault('auto_gains', []).append(dict(arrow=arrow, label=label, leader=leader_artist,
                                                   path_pt=path, points_pt=points))


def add_gain(fig, spec, artists, config, font_dir):
    """Anchor a cubic gain arrow to two current bar values; derive its label from data."""
    spec=merge(config['gain_defaults'],spec)
    before,after=artists[spec['from']],artists[spec['to']]
    if before['axis'] is not after['axis']:
        raise ValueError('Gain arrows must connect bars in one panel')
    if not before['vertical']:
        raise ValueError('Gain arrows currently require vertical panels')
    if spec['auto_layout']:
        return add_auto_gain(fig, spec, artists, config, font_dir)
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
            rr = validate_capacity(rr, style['baseline'], style['capacity']['field'])
            rr = validate_increment(rr, style['baseline'], style['orientation'], style['increment']['field'])
            xx = positions(rr, style)
            limits, ticks = panel_axis(rr, style, rect[3], config)
            if not isinstance(limits, (list, tuple)) or len(limits) != 2:
                raise ValueError('limits must be [lower, upper] or "auto"')
            if isinstance(ticks, str):
                raise ValueError('ticks must be a list or "auto"')
            ticks = list(ticks)
            if not ticks:
                raise ValueError('ticks must not be empty')
            if limits[0] >= limits[1] or not limits[0] <= style['baseline'] <= limits[1]:
                raise ValueError('Invalid numeric limits or baseline')
            if any(r['value'] < limits[0] or r['value'] > limits[1] for r in rr):
                raise ValueError(f'Numeric limits clip bar heights in {panel["id"]}; expand limits explicitly')
            if not style['allow_interval_clipping'] and any(r.get('low',r['value']) < limits[0] or r.get('high',r['value']) > limits[1] for r in rr):
                raise ValueError(f'Numeric limits clip data in {panel["id"]}; expand limits explicitly')
            if any(r.get('capacity', r['value']) > limits[1] for r in rr):
                raise ValueError(f'Numeric limits clip capacity in {panel["id"]}; expand limits explicitly')
            catlim = panel.get('category_limits', [xx.min()-style['bar_width']/2-style['category_margin'],
                                                  xx.max()+style['bar_width']/2+style['category_margin']])
            if vertical:
                ax.set(xlim=catlim, ylim=limits, yticks=ticks, xticks=xx)
                ax.set_yticklabels([format(v,style['tick_format']) for v in ticks])
            else:
                ax.set(ylim=catlim, xlim=limits, xticks=ticks, yticks=xx)
                ax.set_xticklabels([format(v,style['tick_format']) for v in ticks])
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
                value_stop = limits[1] if grid['value_stop'] == 'auto' else grid['value_stop']
                value_step = (limits[1]-limits[0])/10 if grid['value_step'] == 'auto' else grid['value_step']
                cat_extent = rect[2] if vertical else rect[3]
                if grid['spacing_pt'] <= 0 or value_step <= 0:
                    raise ValueError('Grid spacing must be positive')
                point_count = (cat_extent/grid['spacing_pt']+1)*((min(value_stop,limits[1])-limits[0])/value_step+1)
                if point_count > grid['max_points']:
                    raise ValueError('Grid is too dense; increase spacing or explicitly raise grid.max_points')
                step = grid['spacing_pt'] / cat_extent * (catlim[1]-catlim[0])
                gx = np.arange(catlim[0], catlim[1]+step*.001, step)
                gy = np.arange(limits[0], min(value_stop,limits[1])+value_step*.001,value_step)
                mx,my = np.meshgrid(gx,gy)
                ax.scatter(mx if vertical else my, my if vertical else mx, s=grid['size'],
                           color=grid['color'], alpha=grid['alpha'], edgecolors='none', zorder=0, clip_on=True)
            elif grid['kind'] == 'lines':
                linestyle=tuple(grid['linestyle']) if isinstance(grid['linestyle'],list) else grid['linestyle']
                grid_axis={'value':value_axis,'category':category_axis,'both':'both'}.get(grid.get('axis','value'))
                if grid_axis is None:
                    raise ValueError('grid.axis must be value, category or both')
                ax.set_axisbelow(True); ax.grid(axis=grid_axis,color=grid['color'],alpha=grid['alpha'],
                                               linewidth=grid['linewidth'],linestyle=linestyle)
            elif grid['kind'] != 'none':
                raise ValueError('grid.kind must be dots, lines, or none')
            for ref in style.get('reference_lines', []):
                value = float(ref['value'])
                color = ref.get('color', '#6B7280')
                ax.axhline(value, color=color, linestyle=ref.get('linestyle', '--'),
                           linewidth=ref.get('linewidth', .8),
                           alpha=opacity(ref.get('alpha', 1), 'reference.alpha'), zorder=1)
                if ref.get('label'):
                    ax.text(ref.get('label_x', .98), value, ref['label'], transform=ax.get_yaxis_transform(),
                            ha=ref.get('label_ha', 'right'), va='bottom', color=color,
                            bbox={'facecolor': config['figure']['background'], 'edgecolor': 'none',
                                  'pad': 1.2, 'alpha': .9},
                            fontproperties=font(config, ref.get('font', 'regular'), ref.get('size', 7), font_dir),
                            zorder=6, clip_on=False)
            for x, row in zip(xx, rr):
                palette = config['palette'][row['series']]
                fill, edge = bar_colors(palette, style)
                capacity_bar = capacity_label = None
                if style['capacity']['field'] is not None:
                    cs = style['capacity']
                    outline = dict(facecolor='none', edgecolor=palette['edge'],
                                   linewidth=cs['edge_width'], linestyle=cs['linestyle'],
                                   alpha=opacity(cs['alpha'], 'capacity.alpha'), zorder=1)
                    if vertical:
                        capacity_bar = ax.bar(x,row['capacity']-style['baseline'],
                                              width=style['bar_width'],bottom=style['baseline'],**outline)[0]
                    else:
                        capacity_bar = ax.barh(x,row['capacity']-style['baseline'],
                                               height=style['bar_width'],left=style['baseline'],**outline)[0]
                    capacity_bar.set_gid('capacity-'+row['id'])
                    capacity_label = ax.annotate(capacity_text(row, cs),
                        (x,row['capacity']) if vertical else (row['capacity'],x),
                        xytext=(0,style['value_pad']) if vertical else (style['value_pad'],0),
                        textcoords='offset points',ha='center' if vertical else 'left',
                        va='baseline' if vertical else 'center',
                        color=style['value_color'] or palette.get('label',palette['edge']),
                        fontproperties=font(config,style['value_font'],style['value_size'],font_dir),
                        annotation_clip=False)
                    capacity_label.set_gid('capacity-'+row['id']+'-label')
                common = dict(color=fill, edgecolor=edge, linewidth=style['bar_edge_width'],
                              hatch=palette.get('hatch',style['hatch']),zorder=2)
                increment = {}
                if style['increment']['field'] is not None:
                    increment = draw_increment(ax, x, row, style, config, palette)
                    bar = increment['bar']
                elif vertical:
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
                if row.get('replicates'):
                    values = row['replicates']
                    if isinstance(values, str):
                        values = [float(v) for v in values.split('|')]
                    offsets = [(i - (len(values)-1)/2) * style['bar_width'] * .18 for i in range(len(values))]
                    if vertical:
                        ax.scatter([x + o for o in offsets], values, s=8, color=fill, edgecolors='white',
                                   linewidths=.3, alpha=.75, zorder=5)
                    else:
                        ax.scatter(values, [x + o for o in offsets], s=8, color=fill, edgecolors='white',
                                   linewidths=.3, alpha=.75, zorder=5)
                label = None
                if style['value_labels'] or increment:
                    anchor = row.get('high',row['value']) if style['value_anchor']=='high' else row['value']
                    value_text = increment_text(row, style['increment']['label_format']) if increment else format(row['value'],style['value_format'])
                    label=ax.annotate(value_text,
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
                                      'value':row['value'],'series':row['series'],'group':row['group'],'vertical':vertical,
                                      'capacity_bar':capacity_bar,'capacity_label':capacity_label}
                if increment:
                    artists[row['id']].update(increment, total_label=label)
                    label.set_gid('increment-'+row['id']+'-total-label')
                    add_increment_label(fig, ax, x, row, artists[row['id']], style, config, palette, font_dir)
            add_legend(fig,ax,panel,rr,style,config,font_dir)
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
        renderer = fig.canvas.get_renderer()
        tight = fig.get_tightbbox(renderer)
        tolerance = 0.5 / 72
        if (tight.x0 < -tolerance or tight.y0 < -tolerance or
                tight.x1 > fig.get_figwidth() + tolerance or
                tight.y1 > fig.get_figheight() + tolerance):
            warnings.warn('Some text or legend extends outside the figure; adjust layout margins or font sizes', UserWarning)
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
    parser.add_argument('--list-presets',action='store_true',help='List styles, layouts, sizes, palettes and font profiles')
    for key in ('style','layout','size','palette','font'):
        parser.add_argument('--'+key,help=f'Select a {key} preset; explicit config fields still win')
    parser.add_argument('--svg-text',dest='svg_text',action='store_true',default=None,help='Keep SVG text editable (default)')
    parser.add_argument('--svg-paths',dest='svg_text',action='store_false',help='Convert SVG text to paths for submission')
    parser.add_argument('--resolved-config',type=Path,help='Write the complete resolved configuration for fine adjustments')
    args=parser.parse_args()
    if args.defaults: print(json.dumps(DEFAULTS,indent=2));return
    if args.list_presets:
        print(json.dumps({section:{key:value['description'] for key,value in choices.items()}
                          for section,choices in preset_catalog().items() if section in ('styles','layouts','sizes','palettes','fonts')},
                         ensure_ascii=False,indent=2));return
    if args.config is None and args.data is None: parser.error('Supply --config or --data')
    config=read_config(args.config) if args.config else {'preset':{}}
    frozen=bool(config.get('frozen_config'))
    if frozen and any(getattr(args,key) is not None for key in ('style','layout','size')):
        parser.error('This config preserves measured panel geometry; --style/--layout/--size would re-layout it. Use --palette/--font, or start from examples/style-guide.')
    if not frozen:
        for key in ('style','layout','size','palette','font'):
            if getattr(args,key) is not None: config.setdefault('preset',{})[key]=getattr(args,key)
    if args.data is None and 'data' not in config: parser.error('Configuration needs data or --data')
    data=args.data or args.config.parent/config['data']
    rows=load_data(data)
    config=resolve_config(config,rows)
    if args.palette: apply_palette_selection(config,rows,args.palette)
    if args.font: apply_font_selection(config,args.font)
    for path in args.set_file: config=apply_override_file(config,path)
    for assignment in args.set: apply_override(config,assignment)
    if args.svg_text is not None: config['figure']['svg_text']=args.svg_text
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
