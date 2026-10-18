"""Compare categorical palettes in actual render.py charts, not swatches alone.

python scripts/palette_audit.py --config examples/palette-study/config.json
Metrics are diagnostics, not an aesthetic score or accessibility certification.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import to_rgb, to_hex
import numpy as np
from colorspacious import cspace_convert

from render import build_figure, export_figure, load_data, resolve_config


def composite(colors, alpha=1., background='#ffffff'):
    if not 0 < alpha <= 1:
        raise ValueError('fill_alpha must be in (0, 1]')
    rgb = np.array([to_rgb(c) for c in colors])
    return rgb*alpha + np.array(to_rgb(background))*(1-alpha)


def luminance(rgb):
    rgb = np.asarray(rgb)
    linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    return linear @ [.2126, .7152, .0722]


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (np.maximum(a, b)+.05)/(np.minimum(a, b)+.05)


def simulate(rgb, mode):
    if mode == 'normal':
        return np.asarray(rgb)
    if mode == 'grayscale':
        y = luminance(rgb)
        srgb = np.where(y <= .0031308, y*12.92, 1.055*y**(1/2.4)-.055)
        return np.repeat(srgb[..., None], 3, axis=-1)
    if mode not in ('protanomaly', 'deuteranomaly', 'tritanomaly'):
        raise ValueError(f'Unsupported simulation: {mode}')
    # Direction follows the Colorspacious tutorial; reverse conversion is wrong.
    return np.clip(cspace_convert(rgb, {'name':'sRGB1+CVD', 'cvd_type':mode,
                                      'severity':100}, 'sRGB1'), 0, 1)


def separation(rgb):
    if len(rgb) < 2:
        raise ValueError('Need at least two colours')
    ucs = cspace_convert(rgb, 'sRGB1', 'CAM02-UCS')
    d = np.linalg.norm(ucs[:, None, :]-ucs[None, :, :], axis=-1)
    d[np.diag_indices_from(d)] = np.inf
    a, b = np.unravel_index(d.argmin(), d.shape)
    return float(d[a,b]), [int(a)+1, int(b)+1]


def evaluate(candidate, settings):
    colors = candidate['colors']
    if len(colors) != 5 or len(set(c.lower() for c in colors)) != 5:
        raise ValueError('This controlled study requires five unique colours')
    rgb = composite(colors, candidate['fill_alpha'], settings['background'])
    metrics = {'id':candidate['id'], 'family':candidate['family'],
               'name':candidate['name'], 'fill_alpha':candidate['fill_alpha']}
    for mode in ('normal','protanomaly','deuteranomaly','tritanomaly','grayscale'):
        for count in (3,5):
            distance, pair = separation(simulate(rgb[:count], mode))
            metrics[f'{mode}_{count}'] = distance
            metrics[f'{mode}_{count}_pair'] = '-'.join(map(str,pair))
    metrics['fill_background_min'] = float(contrast(rgb, to_rgb(settings['background'])).min())
    metrics['outline_background'] = float(contrast(to_rgb(settings['outline']), to_rgb(settings['background'])))
    metrics['text_background'] = float(contrast(to_rgb(settings['text']), to_rgb(settings['background'])))
    metrics['black_inside_min'] = float(contrast(to_rgb(settings['text']), rgb).min())
    metrics['hatch_fill_min'] = float(contrast(to_rgb(settings['outline']), rgb).min())
    ucs = cspace_convert(rgb,'sRGB1','CAM02-UCS')
    metrics['lightness_span'] = round(float(np.ptp(ucs[:,0])),3)
    metrics['chroma_mean'] = round(float(np.linalg.norm(ucs[:,1:],axis=1).mean()),3)
    gates = settings['gates']
    # Heuristic triage for this white-background, outlined bar study only.
    for count in (3,5):
        reasons=[]
        metrics[f'fill_background_min_{count}'] = float(contrast(rgb[:count], to_rgb(settings['background'])).min())
        metrics[f'hatch_fill_min_{count}'] = float(contrast(to_rgb(settings['outline']), rgb[:count]).min())
        if metrics[f'normal_{count}'] < gates['normal_min']:
            reasons.append('normal-neighbours')
        if min(metrics[f'{m}_{count}'] for m in ('protanomaly','deuteranomaly','tritanomaly')) < gates['cvd_min']:
            reasons.append('cvd-neighbours')
        if metrics[f'fill_background_min_{count}'] < gates['fill_background_min']:
            reasons.append('near-white-fill')
        if metrics['outline_background'] < gates['outline_contrast']:
            reasons.append('outline-contrast')
        if metrics['text_background'] < gates['text_contrast']:
            reasons.append('text-contrast')
        metrics[f'flags_{count}'] = ';'.join(reasons)
        metrics[f'hatch_caution_{count}'] = metrics[f'hatch_fill_min_{count}'] < gates['hatch_contrast']
    metrics['effective_colors'] = ' '.join(to_hex(c) for c in rgb)
    return metrics


def study_board(candidates, rows, settings, title, simulations=False, review=False):
    """All bars, including overlaid lower regions, use the existing renderer.

    Lower values are independent heights from zero, not additive components.
    The diagram tests the screenshot's visual layering; chemistry is not inferred.
    """
    cell_w, cell_h, margin, top = 286, 178, 24, 55
    columns = 2 if not simulations else 3
    variants = [('normal',5),('normal',3)] if not simulations else [
        ('normal',5),('deuteranomaly',5),('grayscale',5)]
    width = margin*2 + cell_w*columns
    height = top + len(candidates)*cell_h + 24
    config = {
        'preset':{'style':'paper-clean','layout':'grouped','palette':'tol-bright','font':'sans'},
        'figure':{'size_pt':[width,height],'dpi':140,'formats':['png','pdf','svg'], 'svg_text':False},
        'palette':{}, 'panels':[],
        'panel_defaults':{'limits':[0,1.0],'ticks':[0,.5,1.0], 'tick_format':'.1f',
            'position_mode':'data','category_mode':'group','category_size':7,'tick_size':7,
            'bar_width':.7,'bar_edge_width':.45,'bar_fill_alpha':1,'bar_edge_alpha':1,
            'spines':['bottom'],'ylabel':'','value_labels':False,
            'grid':{'kind':'lines','linewidth':.4,'color':'#dce1e6','alpha':.6}},
        'legend_defaults':{'show':False}, 'rc':{'hatch.linewidth':.35},
        'annotations':[
            {'text':title,'position_pt':[margin,height-22],'size':13,'font':'bold'},
            {'text':'Same data and geometry  |  white background  |  LAYOUT TEST - synthetic values',
             'position_pt':[margin,height-38],'size':7.5,'color':'#596473'},
            {'text':'Colour distance is a diagnostic, not a beauty score. Lower hatching: independent overlaid heights.',
             'position_pt':[margin,10],'size':7,'color':'#596473'}]}
    combined=[]
    choices={x['id']:x for x in settings.get('shortlist',[])}
    for index,candidate in enumerate(candidates):
        rgb = composite(candidate['colors'],candidate['fill_alpha'],settings['background'])
        for col,(mode,count) in enumerate(variants):
            xx=margin+col*cell_w
            yy=height-top-(index+1)*cell_h+32
            pid=f'{index}-{col}'
            effective=simulate(rgb,mode)
            name=candidate.get('display_name',candidate['name'])
            name=name.replace('glasbey_bw_', 'gb_').replace('scientific-colour-maps','SCM')
            caption=f'{candidate["id"]}  {name}  a={candidate["fill_alpha"]:g}'
            config['annotations'].append({'text':caption,'position_pt':[xx+22,yy+125],'size':8,'font':'bold'})
            descriptor=(f'{count} series / '+('grouped' if count==5 else 'lower region hatched')) if not simulations else mode
            note=choices.get(candidate['id'],{}) if review else {}
            caution=(count==5 and note.get('recommended_series')==3) or (count==3 and not note.get('layered',True))
            if review and not simulations and caution:
                descriptor += ' / '+('prefer 3 series' if count==5 else 'hatch needs adjustment')
            config['annotations'].append({'text':descriptor,'position_pt':[xx+22,yy+112],'size':7,'color':'#9b5837' if caution else '#596473'})
            config['panels'].append({'id':pid,'rect_pt':[xx+23,yy+12,cell_w-42,90]})
            for series in range(count):
                key=f'{pid}-s{series}'
                config['palette'][key]={'fill':to_hex(effective[series]), 'edge':settings['outline'], 'label':settings['text']}
                config['palette'][key+'-lower']={**config['palette'][key],'hatch':'////'}
            for row in rows:
                s=int(row['series'][1:])-1
                if s>=count: continue
                item=copy.deepcopy(row)
                item['id']=pid+'-'+row['id'];item['panel']=pid;item['series']=f'{pid}-s{s}'
                item['x']=(int(row['group'][1:])-1)*(count+.85)+s
                combined.append(item)
            if count==3:
                for row in rows:
                    s=int(row['series'][1:])-1
                    if s>=count: continue
                    item=copy.deepcopy(row)
                    item['id']=pid+'-'+row['id']+'-lower';item['panel']=pid;item['series']=f'{pid}-s{s}-lower'
                    item['x']=(int(row['group'][1:])-1)*(count+.85)+s
                    item['value']=float(row['lower']);combined.append(item)
    # The palette is already composed per panel. Avoid default preset capacity limits.
    config.pop('preset')
    from render import preset_catalog, merge
    fonts=preset_catalog()['fonts']['sans']['roles']
    config['fonts']=copy.deepcopy(fonts)
    config=merge(preset_catalog()['styles']['paper-clean']['config'], config)
    return resolve_config(config,combined), combined


def swatch_board(candidates, settings):
    fig,axes=plt.subplots(len(candidates),1,figsize=(8, len(candidates)*.72+.5),squeeze=False)
    for ax,candidate in zip(axes.flat,candidates):
        effective=composite(candidate['colors'],candidate['fill_alpha'],settings['background'])
        ax.set_xlim(0,8);ax.set_ylim(0,1);ax.axis('off')
        ax.text(0,.65,f'{candidate["id"]}  {candidate.get("display_name",candidate["name"])}',fontsize=8,weight='bold')
        ax.text(0,.25,f'fill alpha {candidate["fill_alpha"]:g}',fontsize=7,color='#596473')
        for j,c in enumerate(effective):
            ax.add_patch(plt.Rectangle((3+j,.40),.88,.55,facecolor=c,edgecolor=settings['outline'],linewidth=.5))
            ax.text(3+j,.15,to_hex(c).upper(),fontsize=7)
    fig.tight_layout(pad=.7)
    return fig


def overview(candidates, settings):
    """Compact index; full-size grouped/layered comparisons are in the PDF."""
    fig,axes=plt.subplots(10,5,figsize=(15,18))
    for ax, pair in zip(axes.flat,zip(candidates[::2],candidates[1::2])):
        ax.set_xlim(0,5);ax.set_ylim(0,2.6);ax.axis('off')
        ax.text(0,2.15,pair[0].get('display_name',pair[0]['name']),fontsize=9,weight='bold')
        for i,candidate in enumerate(pair):
            ax.text(0,1.72-i*.85,candidate['id']+f' / alpha {candidate["fill_alpha"]:g}',fontsize=7,color='#596473')
            for j,c in enumerate(composite(candidate['colors'],candidate['fill_alpha'],settings['background'])):
                ax.add_patch(plt.Rectangle((j,1.02-i*.85),.91,.55,facecolor=c,edgecolor=settings['outline'],linewidth=.4))
    fig.suptitle('100 candidates = 50 distinct five-colour sets x 2 fill strengths',fontsize=16,y=.998)
    fig.tight_layout(pad=1)
    return fig


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--metrics-only',action='store_true')
    parser.add_argument('--shortlist-only',action='store_true',help='Keep the already rendered full candidate PDF')
    args=parser.parse_args()
    directory=args.config.parent
    settings=json.loads(args.config.read_text(encoding='utf8'))
    candidates=json.loads((directory/settings['candidates']).read_text(encoding='utf8'))
    ids=[c['id'] for c in candidates]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate candidate IDs')
    metrics=[evaluate(c,settings) for c in candidates]
    ranking=sorted(metrics,key=lambda m:(bool(m['flags_5']),-min(m[f'{s}_5'] for s in ('protanomaly','deuteranomaly','tritanomaly')),-m['normal_5']))
    for rank,m in enumerate(ranking,1): m['separability_rank_5']=rank
    with (directory/'metrics.csv').open('w',encoding='utf8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(metrics[0]));writer.writeheader();writer.writerows(metrics)
    if args.metrics_only: return
    rows=load_data(directory/settings['data'])
    def save_board(items,title,stem,pdf,simulations=False,preview_only=False):
        config,data=study_board(items,rows,settings,title,simulations,review=not preview_only)
        fig,_=build_figure(config,data)
        pdf.savefig(fig)
        if preview_only: config['figure']['formats']=['png']
        export_figure(fig,config,directory/stem)
        plt.close(fig)
    if not args.shortlist_only:
        with plt.rc_context({'pdf.fonttype':42}), PdfPages(directory/'all-candidates.pdf') as pdf:
            for start in range(0,len(candidates),5):
                save_board(candidates[start:start+5],f'Palette study / candidates {start+1}-{min(start+5,len(candidates))}',
                           f'candidates-{start//5+1:02}',pdf,preview_only=True)
    fig=overview(candidates,settings)
    export_figure(fig,{'figure':{'formats':['png','pdf'],'dpi':140,'background':'white','svg_text':False}},directory/'overview')
    plt.close(fig)
    selected=settings.get('shortlist',[])
    if selected:
        lookup={c['id']:c for c in candidates}
        chosen=[lookup[x['id']] for x in selected]
        recipes=[]
        for candidate,note in zip(chosen,selected):
            colors=[to_hex(c) for c in composite(candidate['colors'],candidate['fill_alpha'],settings['background'])]
            recipes.append({**candidate,**note,'effective_colors_on_white':colors,
                'render_override':{'panel_defaults':{'bar_fill_alpha':1,'bar_edge_alpha':1,'bar_edge_width':.45},
                    'palette':{f'S{i+1}':{'fill':color,'edge':settings['outline'],'label':settings['text']}
                               for i,color in enumerate(colors)}}})
        (directory/'selected-palettes.json').write_text(json.dumps(recipes,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        with plt.rc_context({'pdf.fonttype':42}), PdfPages(directory/'shortlist.pdf') as pdf:
            for start in range(0,len(chosen),5):
                save_board(chosen[start:start+5],'Shortlist / visual selection after diagnostic screening',
                           f'shortlist-{start//5+1}',pdf)
            for start in range(0,len(chosen),5):
                save_board(chosen[start:start+5],'Shortlist / normal, simulated deuteranopia, grayscale',
                           f'visibility-{start//5+1}',pdf,True)
        fig=swatch_board(chosen,settings)
        export_figure(fig,{'figure':{'formats':['png','pdf','svg'],'dpi':180,'background':'white','svg_text':True}},directory/'swatches')
        plt.close(fig)
    print(json.dumps({'candidates':len(candidates),'shortlisted':len(selected)}))


if __name__=='__main__':
    main()
