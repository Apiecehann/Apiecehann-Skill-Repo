"""Compose comparison pages with the same render.py artists, including vector PDFs.

python scripts/catalog.py --config examples/style-guide/gallery.json
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from render import (build_figure, export_figure, load_data, merge, panel_rectangles,
                    preset_catalog, read_config, resolve_config)


def prefix_fonts(value, prefix):
    if isinstance(value, dict):
        return {key: prefix+item if (key == 'font' or key.endswith('_font')) and isinstance(item,str)
                else prefix_fonts(item,prefix) for key,item in value.items()}
    if isinstance(value, list):
        return [prefix_fonts(item,prefix) for item in value]
    return value


def compose_board(board, directory):
    """Place single-panel recipes side by side, preserving their physical sizes."""
    cases = []
    for case in board['cases']:
        path = directory/case['config']
        raw = merge(read_config(path),case.get('override',{}))
        rows = load_data(path.parent/raw['data'])
        config = resolve_config(raw,rows)
        if len(config['panels']) != 1 or config['icons'] or config['bands']:
            raise ValueError('Comparison recipes require one panel and no icons/group bands')
        cases.append((case,config,rows))
    if not cases:
        raise ValueError('Comparison board needs at least one case')
    columns = min(board.get('columns',3),len(cases))
    if columns < 1:
        raise ValueError('Comparison columns must be positive')
    row_count = math.ceil(len(cases)/columns)
    margin, gutter, header, footer, caption = 18, 20, 64, 28, 30
    cell_w = max(config['figure']['size_pt'][0] for _,config,_ in cases)
    cell_h = max(config['figure']['size_pt'][1] for _,config,_ in cases)+caption
    width = margin*2+columns*cell_w+(columns-1)*gutter
    height = header+row_count*cell_h+(row_count-1)*gutter+footer
    result = {
        'figure':{'size_pt':[width,height],'dpi':170,'formats':['png','pdf','svg'],'background':'white'},
        'fonts':copy.deepcopy(preset_catalog()['fonts']['sans']['roles']),
        'palette':{},'panels':[],'gains':[],
        'annotations':[
            {'text':board['title'],'position_pt':[margin,height-24],'size':16,'font':'bold'},
            {'text':board.get('subtitle',''),'position_pt':[margin,height-42],'size':9,'color':'#596473'},
            {'text':'Shared render.py  /  source measurements preserved  /  editable vector output',
             'position_pt':[margin,11],'size':7.5,'color':'#687280'}
        ]
    }
    combined_rows = []
    for index,(case,config,rows) in enumerate(cases):
        prefix = f'case{index}-'
        column,row = index%columns,index//columns
        x = margin+column*(cell_w+gutter)
        y = height-header-(row+1)*cell_h-row*gutter
        result['annotations'].append({'text':case['title'],'position_pt':[x+config['layout']['left_pt'],y+cell_h-11],
                                      'size':11,'font':'bold'})
        result['fonts'].update({prefix+key:value for key,value in config['fonts'].items()})
        result['palette'].update({prefix+key:value for key,value in config['palette'].items()})
        panel = copy.deepcopy(config['panels'][0])
        panel['id'] = prefix+panel['id']
        rect = list(panel_rectangles(config))[0]
        panel['rect_pt'] = [x+rect[0],y+rect[1],rect[2],rect[3]]
        panel['style'] = prefix_fonts(merge(config['panel_defaults'],panel.get('style',{})),prefix)
        legend = merge(config['legend_defaults'],panel.get('legend',{}))
        if legend['order'] is not None:
            legend['order'] = [prefix+key for key in legend['order']]
        legend['labels'] = {prefix+key:value for key,value in legend['labels'].items()}
        for series in dict.fromkeys(row['series'] for row in rows):
            legend['labels'].setdefault(prefix+series,series)
        panel['legend'] = prefix_fonts(legend,prefix)
        for field in ('tokens','readable_tokens','token_shift_pt'):
            if field in panel:
                panel[field] = {prefix+key:prefix_fonts(value,prefix) for key,value in panel[field].items()}
        result['panels'].append(panel)
        for value in rows:
            item = copy.deepcopy(value)
            for key in ('id','panel','series'): item[key] = prefix+item[key]
            combined_rows.append(item)
        for gain in config['gains']:
            item = prefix_fonts(merge(config['gain_defaults'],gain),prefix)
            for key in ('from','to'): item[key] = prefix+item[key]
            result['gains'].append(item)
        for annotation in config['annotations']:
            item = prefix_fonts(copy.deepcopy(annotation),prefix)
            item['position_pt'] = [x+item['position_pt'][0],y+item['position_pt'][1]]
            if item.get('palette'): item['palette'] = prefix+item['palette']
            result['annotations'].append(item)
    return resolve_config(result,combined_rows),combined_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,help='Output directory; defaults to the recipe directory')
    args = parser.parse_args()
    recipe = json.loads(args.config.read_text(encoding='utf8'))
    destination = args.output or args.config.parent
    destination.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'pdf.fonttype':42}), PdfPages(destination/'catalog.pdf') as pdf:
        for board in recipe['boards']:
            config,rows = compose_board(board,args.config.parent)
            figure,artists = build_figure(config,rows)
            export_figure(figure,config,destination/board['name'])
            pdf.savefig(figure)
            plt.close(figure)
            print(json.dumps({'board':board['name'],'panels':len(config['panels']),'bars':len(artists)}))


if __name__ == '__main__':
    main()
