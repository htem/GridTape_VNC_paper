#!/usr/bin/env python3

import sys
import os

import numpy as np
import matplotlib.pyplot as plt

# GridTape-VNC_ms/figures_and_analysis/python_utilities/nblast_score_files.py
sys.path.append('../python_utilities')
import nblast_score_files as nsf
# GridTape-VNC_ms/figures_and_analysis/python_utilities/bundles.py
import bundles

# --- Motor neuron functions --- # 
lm_motor_neurons = {'81A07': 625346, '22A08': 625284, '35C09': 625300,
                  '21G01': 625254, '33C10_L': 625223, '33C10_R': 625239, '56H01': 625315}
motor_subtypes = {bundles.lengthen(bundle): (bundles.colors[bundle], bundle+' neuron')
                  for bundle in bundles.colors}
motor_scores_fn = '../nblast_scores/catmaid_nblast_scores_id79_LMxEM_leftT1_motorNeurons_inNeuropil.csv'
def motor(show=True, save_format=None):
    def _plot_motor_correspondence_scores(**kwargs):
        kwargs.update({'save_dir': 'motor_neuron_correspondence_score_plots'})
        _plot_top_hit_scores(motor_scores_fn,
                             neurons_to_plot=lm_motor_neurons,
                             subtypes=motor_subtypes,
                             **kwargs)
    if isinstance(show, str):
        if show.lower() in ['', 'false']:
            show = False
        else:
            show = True
    _plot_motor_correspondence_scores(mode='all motor', show=show, save_format=save_format)
    _plot_motor_correspondence_scores(mode='zoom motor', show=show, save_format=save_format)


# --- Sensory neuron functions --- #
sensory_scores_fn = '../nblast_scores/catmaid_nblast_scores_id93_LMxEM_leftT1_sensoryNeurons.csv'
coarse_sensory_subtypes = {'bristle': ('#4dbeee', 'bristle neuron'),
                           'hair plate': ('#edb120', 'hair plate neuron'),
                           'chordotonal neuron': ('#d95319', 'chordotonal neuron'),
                           'campaniform sensillum': ('#7e2f8e', 'campaniform sensillum neuron')}
fine_sensory_subtypes = {'bristle': ('#4dbeee', 'bristle neuron'),
                         'hair plate': ('#7e2f8e', 'hair plate neuron'),
                         'T1 leg club chordotonal neuron': ('#ff0000', 'Club chordotonal neuron'),
                         'T1 leg claw chordotonal neuron': ('#00ff00', 'Claw chordotonal neuron'),
                         'T1 leg hook chordotonal neuron': ('#0000ff', 'Hook chordotonal neuron'),
                         'campaniform sensillum': ('#edb120', 'campaniform sensillum neuron')}
def sensory(show=True, save_format=None):
    def _plot_sensory_correspondence_scores(**kwargs):
        kwargs.update({'save_dir': 'sensory_neuron_correspondence_score_plots'})
        _plot_top_hit_scores(sensory_scores_fn,
                             subtypes=coarse_sensory_subtypes,
                             **kwargs)
    if isinstance(show, str):
        if show.lower().strip(',') in ['', 'false']:
            show = False
        else:
            show = True
    _plot_sensory_correspondence_scores(mode='all sensory', show=show, save_format=save_format)
    #_plot_top_sensory_hit_scores(mode='zoom sensory', show=show, save_format=save_format) #Not currently a thing


chordotonal_scores_fn = '../nblast_scores/catmaid_nblast_scores_id90_LMxEM_leftT1_club_claw_hook.csv'
chordotonal_subtypes = {'T1 leg club chordotonal neuron': ('#00cc00', 'Club chordotonal neuron'),
                        'T1 leg claw chordotonal neuron': ('#ff0000', 'Claw chordotonal neuron'),
                        'T1 leg hook chordotonal neuron': ('#7e2f8e', 'Hook chordotonal neuron')}
                        #'T1 leg unclassified chordotonal neuron': ('#000000', 'unclassified'),
                        #'neck chordotonal neuron': ('#000000', 'Neck chordotonal neuron'),
def chordotonal(show=True, save_format=None):
    def _plot_chordotonal_correspondence_scores(**kwargs):
        kwargs.update({'save_dir': 'chordotonal_neuron_correspondence_score_plots'})
        _plot_top_hit_scores(chordotonal_scores_fn,
                             subtypes=chordotonal_subtypes,
                             **kwargs)
    if isinstance(show, str):
        if show.lower().strip(',') in ['', 'false']:
            show = False
        else:
            show = True
    _plot_chordotonal_correspondence_scores(mode='all chordotonal', show=show, save_format=save_format)
    _plot_chordotonal_correspondence_scores(mode='top 50 chordotonal', show=show, save_format=save_format)



# --- General plotting function --- #
def _plot_top_hit_scores(scores_fn,
                         neurons_to_plot=None,
                         subtypes=None,
                         show=True,
                         save_format=None,
                         **kwargs):
    """
    neurons_to_plot must be a dict mapping neuron names (as strings) to their
    skeleton ids (as ints). If None, each column of the scores file will be
    treated as a neuron to plot.
    subtypes must be a dict mapping skeleton ids (as ints) to a 2-tuple where
    the first entry is the color to be used for that subtype (as a hex string)
    and the second entry is the figure legend label for that subtype (as str)
    """
    scores = nsf.load_scores(scores_fn)
    info = nsf.pull_neuron_info(scores)
    (headers_are, name_to_skid, skid_to_name, skid_to_annots) = info

    default_dir = 'top_hit_scores_plotted'
    save_dir = kwargs.get('save_dir', default_dir)

    mode = kwargs.get('mode', 'default')
    show_n_hits = kwargs.get('show_n_hits', 0)  # 0 means show all hits
    bbox = kwargs.get('bbox', 'auto')
    marker = kwargs.get('marker', None)
    alpha = kwargs.get('alpha', 1)
    legend_ncol = kwargs.get('legend_ncol', 1)
    bar_mode = kwargs.get('bar_mode', False)
    if mode == 'all motor':
        bbox = 'full'
        xgap = 10
        ygap = 0.1
        fontsize = 6.5
        figwidth = 4
        markersize = 16
        legend_ncol = 3
    elif mode == 'zoom motor':
        show_n_hits = 8
        xgap = 10
        ygap = 0.02
        fontsize = 8
        figwidth = 2.5
        markersize = 25
    elif mode == 'all sensory':
        bbox = 'wide'
        xgap = 50
        ygap = 0.1
        fontsize = 8
        figwidth = 5
        markersize = 18
    elif mode == 'zoom sensory':
        raise ValueError(mode)
    elif 'chordotonal' in mode:
        if mode == 'all chordotonal':
            pass
        elif mode == 'top 50 chordotonal':
            show_n_hits = 50
        xgap = 25
        ygap = 0.1
        fontsize = 8
        figwidth = 3.25
        markersize = 18
    elif mode == 'default':
        fontsize = 8
        figwidth = 4
        markersize = 22
    else:
        raise ValueError('Mode {} not recognized.'.format(mode))
    if bar_mode:
        marker = 'x'

    if neurons_to_plot is None:
        neurons_to_plot = {skid_to_name[skid]: skid for skid in scores.index}

    for neuron in neurons_to_plot:
        skid = neurons_to_plot[neuron]
        top_hits = nsf.get_top_hits(scores, skid, show_n_hits)
        ranks = np.arange(len(top_hits)) + 1
        plt.figure()
        counted = [False] * len(top_hits.index)
        for subtype in subtypes:
            is_this_subtype = [subtype in annots for annots in
                              [skid_to_annots[skid] for skid in top_hits.index]]
            if not any(is_this_subtype):
                continue
            counted = [a or b for a, b in zip(counted, is_this_subtype)]
            plt.scatter(ranks[is_this_subtype],
                        top_hits[is_this_subtype],
                        marker=marker,
                        s=markersize,
                        alpha=alpha,
                        c=subtypes[subtype][0],
                        label=subtypes[subtype][1])
        if not all(counted):
            print('Some hits were not plotted:')
            print(top_hits[[not i for i in counted]])
        if bbox is 'full':
            plt.gca().set(xlim=(len(top_hits) + 1, 0))
            plt.gca().set(ylim=(0, 0.625))
        elif bbox is 'auto':
            plt.gca().set(xlim=(len(top_hits) + 0.5, 0.5))
            #ylim left at default to get automatically set
        elif bbox is 'wide':
            plt.gca().set(xlim=(len(top_hits) + 5, -4))
        else:
            plt.axis(bbox)
        if bar_mode:
            ylim = plt.gca().get_ylim()
            for subtype in subtypes: # have to do this loop after ylim is set above
                is_this_subtype = [subtype in annots for annots in
                                  [skid_to_annots[skid] for skid in top_hits.index]]
                for pt in zip(ranks[is_this_subtype], top_hits[is_this_subtype]):
                    plt.fill_between([pt[0]-0.5, pt[0]+0.5], [-2, -2], [pt[1], pt[1]],
                                     color=subtypes[subtype][0])
            plt.scatter(ranks,
                        top_hits,
                        marker=marker,
                        s=markersize,
                        c='k')
            plt.gca().set(ylim=ylim) # Don't let the plot expand due to the fills

        plt.title(neuron, fontsize=7)
        plt.xlabel('NBLAST score ranking')
        xticks = [1] + list(range(xgap, len(top_hits)-int(xgap/2), xgap)) + [len(top_hits)]
        plt.xticks(xticks)
        plt.ylabel('NBLAST score')
        start, end = plt.gca().get_ylim()
        start -= 1e-8
        end += 1e-8
        plt.gca().yaxis.set_ticks(np.arange(start + ygap - start % ygap,
                                            end + ygap - end % ygap, ygap))
        plt.gcf().set_size_inches(figwidth, 4)
        plt.legend(loc='upper left', ncol=legend_ncol, fontsize=fontsize)
        plt.tight_layout()
        if save_format is not None:
            if save_format == 'png':
                t = False
            else:
                t = True
            os.makedirs(f'{save_dir}/top_{len(top_hits)}_hits', exist_ok=True)
            plt.savefig(f'{save_dir}/top_{len(top_hits)}_hits/'
                        f'{neuron}_top_{len(top_hits)}_hits.{save_format}', transparent=t)
        if show:
            plt.show()


if __name__ == '__main__':
    l = locals()
    public_functions = [f for f in l if callable(l[f]) and f[0] != '_']
    #if len(sys.argv) == 1:
    #    sys.argv.append('generate_motor_neuron_figures')

    if len(sys.argv) == 1 or not sys.argv[1] in public_functions:
        from inspect import signature
        print('Functions available:')
        for f_name in public_functions:
            print('  '+f_name+str(signature(l[f_name])))
            docstring = l[f_name].__doc__
            if not isinstance(docstring, type(None)):
                print(docstring.strip('\n'))
        print('Examples of how to run this script from your terminal:')
        print('python plot_nblast_scores.py motor')
        print('python plot_nblast_scores.py sensory show=False save_format=png')
    else:
        func = l[sys.argv[1]]
        args = []
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                split = arg.split('=')
                kwargs[split[0]] = split[1]
            else:
                args.append(arg)
        func(*args, **kwargs)
