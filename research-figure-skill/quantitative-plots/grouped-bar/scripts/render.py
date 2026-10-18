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
from matplotlib.patches import PathPatch, FancyBboxPatch
import numpy as np

DEFAULTS = {
    'figure': {'size_pt': [540, 180], 'background': 'white', 'dpi': 300,
               'formats': ['png', 'pdf', 'svg'], 'svg_text': False},
    'fonts': {'light': {'family': 'Liberation Sans', 'weight': 'normal', 'file': 'Graphik-Light.ttf'},
              'regular': {'family': 'Liberation Sans', 'weight': 'normal', 'file': 'Graphik-Regular.ttf'},
              'mono': {'family': 'DejaVu Sans Mono', 'weight': 'normal', 'file': 'B612Mono-Regular.ttf'}},
    'palette': {'base': {'fill': '#a1a1a1', 'edge': '#525252', 'label': '#404040'},
                'cue': {'fill': '#fabc00', 'edge': '#da7700', 'label': '#b45300'},
                'rl': {'fill': '#56a2ff', 'edge': '#155dfc', 'label': '#1447e6'},
                'edit': {'fill': '#ff6568', 'edge': '#e40016', 'label': '#bf000f'},
                'answer': {'fill': '#a686ff', 'edge': '#7f22fe', 'label': '#7008e7'}},
    'panel_defaults': {
        'orientation': 'vertical', 'limits': [0, 1.07], 'ticks': [0, .2, .4, .6, .8, 1],
        'tick_format': '.1f', 'tick_size': 9.5, 'tick_length': 4, 'tick_width': .6,
        'tick_pad': 3.5, 'tick_color': '#525252', 'text_color': '#111111',
        'axis_color': '#101828', 'axis_width': .6, 'baseline_width': .8,
        'show_value_ticks': True, 'show_category_ticks': True, 'show_categories': True,
        'category_size': 7.6, 'category_pad': 6, 'category_rotation': 0,
        'label_size': 11.5, 'label_pad': 4, 'ylabel': '',
        'bar_width': .55, 'bar_edge_width': .8, 'bar_alpha': 1, 'hatch': None,
        'group_gap': .8, 'series_gap': .45, 'category_margin': .35,
        'error_width': .7, 'error_color': '#111111', 'error_cap': 2,
        'value_labels': True, 'value_format': '.2f', 'value_size': 10.5,
        'value_pad': 5, 'value_anchor': 'high', 'value_background': True,
        'value_background_pad': .1, 'baseline': 0, 'allow_interval_clipping': False,
        'grid': {'kind': 'dots', 'spacing_pt': 10.5, 'value_step': .1,
                 'value_stop': 1, 'size': .75, 'color': '#bdbdbd', 'alpha': 1, 'max_points': 50000},
        'tokens': {'size': 6.3, 'gap': 2.6, 'padding_em': [.16, .16],
                   'height_em': 1.333333, 'baseline_em': .405, 'rounding': .194444,
                   'edge_width': .4, 'background': '#f5f5f5', 'edge': '#262626',
                   'shadow': True, 'shadow_offset': [.35, -.55], 'shadow_alpha': .28,
                   'offset_pt': 6, 'tint': False},
    },
    'panels': [], 'annotations': [], 'bands': [], 'icons': [],
    'layout': {'columns': 3, 'left_pt': 42, 'right_pt': 8, 'top_pt': 22,
               'bottom_pt': 38, 'column_gap_pt': 30, 'row_gap_pt': 32},
    'rc': {},
}


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result


def apply_override(config, assignment):
    """--set panel_defaults.value_size=9 or --set palette.cue.fill='"#12abcf"'."""
    path, sep, value = assignment.partition('=')
    if not sep:
        raise ValueError('Overrides must be dotted.path=JSON_VALUE')
    value = json.loads(value)
    keys = path.split('.')
    target = config
    for key in keys[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    key = int(keys[-1]) if isinstance(target, list) else keys[-1]
    if isinstance(target, dict) and key not in target:
        raise ValueError(f'Unknown parameter: {path}')
    target[key] = value


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
    return fm.FontProperties(family=spec['family'], weight=spec['weight'], size=size)


def positions(rows, style):
    """Explicit positions preserve measured layouts; otherwise arrange all groups."""
    explicit = ['x' in row for row in rows]
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


def build_figure(config, rows, font_dir=None):
    config = merge(DEFAULTS, config)
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
            value = np.array([r['value'] for r in rr])
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
            for side in ('top', 'right'): ax.spines[side].set_visible(False)
            for side in ('left', 'bottom'):
                ax.spines[side].set_color(style['axis_color']); ax.spines[side].set_linewidth(style['axis_width'])
            ax.spines['bottom' if vertical else 'left'].set_linewidth(style['baseline_width'])
            ax.tick_params(length=style['tick_length'], width=style['tick_width'], pad=style['tick_pad'],
                           color=style['tick_color'], labelcolor=style['text_color'])
            category_axis, value_axis = ('x','y') if vertical else ('y','x')
            ax.tick_params(axis=value_axis, labelleft=style['show_value_ticks'] if vertical else False,
                           labelbottom=style['show_value_ticks'] if not vertical else False)
            ax.tick_params(axis=category_axis, length=style['tick_length'] if style['show_category_ticks'] else 0,
                           pad=style['category_pad'], labelsize=style['category_size'])
            labels = [r.get('label',r['series']) if style['show_categories'] and not panel.get('tokens',{}).get(r['id']) else '' for r in rr]
            (ax.set_xticklabels if vertical else ax.set_yticklabels)(labels, rotation=style['category_rotation'])
            for label in (ax.get_yticklabels() if vertical else ax.get_xticklabels()):
                label.set_fontproperties(font(config,'light',style['tick_size'],font_dir))
            for label in (ax.get_xticklabels() if vertical else ax.get_yticklabels()):
                label.set_fontproperties(font(config,'light',style['category_size'],font_dir))
            if style['ylabel']:
                setter = ax.set_ylabel if vertical else ax.set_xlabel
                setter(style['ylabel'], labelpad=style['label_pad'], color=style['text_color'],
                       fontproperties=font(config,'regular',style['label_size'],font_dir))
            grid = style['grid']
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
                ax.set_axisbelow(True); ax.grid(axis=value_axis,color=grid['color'],alpha=grid['alpha'],linewidth=.5)
            elif grid['kind'] != 'none':
                raise ValueError('grid.kind must be dots, lines, or none')
            for x, row in zip(xx, rr):
                palette = config['palette'][row['series']]
                common = dict(color=palette['fill'], edgecolor=palette['edge'], linewidth=style['bar_edge_width'],
                              alpha=style['bar_alpha'], hatch=palette.get('hatch',style['hatch']),zorder=2)
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
                                       capsize=style['error_cap'],capthick=style['error_width'],zorder=4)
                label = None
                if style['value_labels']:
                    anchor = row.get('high',row['value']) if style['value_anchor']=='high' else row['value']
                    label=ax.annotate(format(row['value'],style['value_format']),
                        (x,anchor) if vertical else (anchor,x),
                        xytext=(0,style['value_pad']) if vertical else (style['value_pad'],0),
                        textcoords='offset points',ha='center' if vertical else 'left',
                        va='baseline' if vertical else 'center',
                        color=palette.get('label',palette['edge']),
                        bbox={'boxstyle':f'square,pad={style["value_background_pad"]}',
                              'facecolor':config['figure']['background'],'edgecolor':'none'} if style['value_background'] else None,
                        fontproperties=font(config,'light',style['value_size'],font_dir),annotation_clip=False)
                if row['id'] in panel.get('tokens',{}):
                    token_label(ax,x,panel['tokens'][row['id']],style,config,palette,font_dir,
                                panel.get('token_shift_pt',{}).get(row['id'],0))
                artists[row['id']] = {'bar':bar,'error':error,'label':label,'x':float(x),'axis':ax}
        for a in config['annotations']:
            color = a.get('color','#111111')
            if a.get('palette'): color=config['palette'][a['palette']][a.get('palette_part','edge')]
            props=dict(ha=a.get('ha','left'),va='baseline',rotation=a.get('rotation',0),rotation_mode='anchor',color=color,
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


def render(config, rows, output, font_dir=None):
    config=merge(DEFAULTS,config)
    fig,artists=build_figure(config,rows,font_dir)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'pdf.fonttype':42,'svg.fonttype':'none' if config['figure']['svg_text'] else 'path'}):
        for ext in config['figure']['formats']:
            if ext not in ('png','pdf','svg'): raise ValueError(f'Unsupported export {ext}')
            fig.savefig(output.with_suffix('.'+ext),dpi=config['figure']['dpi'],facecolor=config['figure']['background'])
    plt.close(fig)
    return len(artists)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--data',type=Path,help='Replace CSV; otherwise resolve config.data relative to config file')
    parser.add_argument('--output',type=Path,help='Output stem; defaults to figure next to config')
    parser.add_argument('--font-dir',type=Path,help='Optional directory with locally licensed font files')
    parser.add_argument('--set',action='append',default=[],metavar='PATH=JSON',help='Override any declared parameter')
    parser.add_argument('--defaults',action='store_true',help='Print complete default parameter groups')
    args=parser.parse_args()
    if args.defaults: print(json.dumps(DEFAULTS,indent=2));return
    if args.config is None: parser.error('--config is required')
    config=merge(DEFAULTS,json.loads(args.config.read_text(encoding='utf8')))
    for assignment in args.set: apply_override(config,assignment)
    for icon in config['icons']:
        if 'image' in icon: icon['image']=str(args.config.parent/icon['image'])
    data=args.data or args.config.parent/config['data']
    rows=load_data(data)
    count=render(config,rows,args.output or args.config.parent/'figure',args.font_dir)
    missing=[name for name,s in config['fonts'].items() if s.get('file') and not
             ((args.font_dir and s.get('file') and (args.font_dir/s['file']).is_file()) or
              (s.get('file') and (Path(__file__).parent/'fonts'/s['file']).is_file()))]
    print(json.dumps({'rendered_bars':count,'font_fallback_roles':missing,'output':str(args.output or args.config.parent/'figure')}))


if __name__=='__main__':
    main()
