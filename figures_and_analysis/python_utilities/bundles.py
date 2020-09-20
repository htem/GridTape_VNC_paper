#!/usr/bin/env python3

import sys

colors = {'L1': '#0000ff',
          'L2': '#00ffff',
          'L3': '#8080ff',
          'L4': '#000080',
          'L5': '#008080',
          'A1': '#800080',
          'A2': '#ff80ff',
          'A3': '#ff00ff',
          'A4': '#8000ff',
          'A5': '#c080ff',
          'V1': '#ffc080',
          'V2': '#800040',
          'V3': '#ff8000',
          'V4': '#ff80c0',
          'V5': '#ff8080',
          'V6': '#ff0000',
          'D1': '#c0c0c0',
          'D2': '#404040'}


def shorten(annotation):
    """
    Converts strings like 'T1 motor neuron V2 bundle' to 'V2'
    """
    if not isinstance(annotation, str):
        return [shorten(a) for a in annotation]
    return annotation.split(' bundle')[0].split(' ')[-1]


def lengthen(bundle, prefix='T1 leg motor neuron'):
    """
    Converts strings like 'V2' to 'T1 motor neuron V2 bundle'
    """
    if not isinstance(bundle, str):
        return [lengthen(b, prefix) for b in bundle]
    if prefix not in ['', None]:
        return prefix + ' ' + bundle + ' bundle'
    else:
        return bundle + ' bundle'


def get_color(bundle):
    """
    Return the color assigned to the given bundle. The argument can be:
    1) A string like 'L2' or 'T1 motor neuron L2 bundle'
    2) A list of strings like those listed in 1)
    3) A list of annotations for a neuron, in which case the bundle
       string will be pulled out and processed
    """
    if not isinstance(bundle, str):
        try:
            bundle = get_bundle_from_annots(bundle)
        except:
            return [get_color(b) for b in bundle]

    try:
        if bundle.endswith(' bundle'):
            return colors[shorten(bundle)]
        else:
            return colors[bundle]
    except:
        raise ValueError('Argument {} not understood'.format(bundle))


def get_bundles_list(nerve=None, form='short', **kwargs):
    """
    Returns the complete list of bundle identifiers, specified
    by the keys of bundles.colors
    """
    if nerve is not None:
        assert nerve in ['L', 'A', 'V', 'D'], 'nerve can only be L, A, V, or D'
        bundles = [b for b in colors.keys() if b[0] == nerve]
    else:
        bundles = colors.keys()

    if form == 'short':
        return [b for b in bundles]
    elif form == 'long':
        return [lengthen(b, **kwargs) for b in bundles]
    else:
        raise ValueError('Form {} not understood. Must be short or long'.format(form))


def count_bundle_members(nerve=None, form='short', side='left'):
    import pymaid
    import pymaid_utils as pu
    pu.source_project.make_global()
    bundles = get_bundles_list(nerve=nerve, form='long')
    counts = {b: len(pymaid.get_skids_by_annotation(
                         [b] + ([side+' soma'] if side in ['left', 'right'] else []),
                         intersect=True
                     )) for b in bundles}
    if form == 'short':
        counts = {shorten(b): count for b, count in counts.items()}
    return counts


def make_bundles_legend(nerve=None, prefix='', show_counts=True, save_format=None, **kwargs):
    """
    Uses matplotlib to create a legend that shows the colors used for
    rendering each bundle
    https://matplotlib.org/3.3.1/gallery/text_labels_and_annotations/custom_legends.html
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    bundles = get_bundles_list(nerve)
    colors = get_color(bundles)
    legend_labels = lengthen(bundles, prefix=prefix)
    if show_counts:
        counts_left = count_bundle_members(nerve=nerve, side='left')
        counts_right = count_bundle_members(nerve=nerve, side='right')
        count_labels = ['(n='+str(i)+' per side)' if i == j
                        else '(n='+str(i)+' L, '+str(j)+' R)'
                        for i, j in zip(counts_left.values(), counts_right.values())]
        legend_labels = [b+' '+c for b, c in zip(legend_labels, count_labels)]



    lw = kwargs.get('lw', 4)
    lines = [Line2D([0], [0], color=color, lw=lw)
             for color in colors]
    plt.legend(lines, legend_labels, **kwargs)
    plt.gcf().set_size_inches(4, 6)
    if save_format is not None:
        save_fn = 'bundles_legend' + ('_{}nerve'.format(nerve) if nerve else '') + '.' + save_format
        print('Saving to ' + save_fn)
        plt.savefig(save_fn)
    plt.show()


def get_bundle_from_skid(skids, form='short', project=None, **kwargs):
    """
    Given a skeleton ID or list of skeleton IDs, return a dict with the
    skeleton IDs as keys and their bundle string as values
    """
    import pymaid
    default_catmaid_project_id = 59
    temp_pid = None
    if project is None:
        project = kwargs.get('project_id', default_catmaid_project_id)
        print(f'Defaulting to using project id {project}')
    if isinstance(project, str):
        project = int(project)
    if isinstance(project, int):
        import pymaid_utils as pu
        temp_pid = pu.source_project.project_id
        if pu.source_project.project_id != project:
            pu.set_source_project_id(project_id)
        project = pu.source_project
    annots = pymaid.get_annotations(skids, remote_instance=project)
    bundles = {int(skid): get_bundle_from_annots(annots[skid], form=form)
               for skid in annots}
    if len(bundles) != len(skids):
        print('WARNING: Some skids returned no results:',
              [skid for skid in skids if skid not in bundles])

    if temp_pid is not None and pu.source_project.project_id != temp_pid:
        pu.set_source_project_id(temp_pid)

    return bundles


def get_bundle_from_annots(annots, form='short'):
    """
    Given a list of annotations for a single neuron, find the annotation
    that specifies the neuron's bundle and return the bundle.
    """
    if isinstance(annots[0], list):
        return [get_bundle_from_annots(x) for x in annots]
    bundle_annots = [annot for annot in annots if annot.endswith(' bundle')]
    if len(bundle_annots) == 1:
        if form == 'long':
            return bundle_annots[0]
        elif form == 'short':
            return shorten(bundle_annots[0])
    else:
        raise ValueError('Argument not understood - is not a list containing'
                ' exactly 1 \'bundle\' annotation:', bundle_annots)


def append_bundles_to_csv(fn, skid_column=0, replace_original=False, project_id=None):
    """
    Given a csv file with a column containing skeleton IDs, append a column
    containing the bundle identifier of that skeleton ID
    """
    assert fn.endswith('.csv')
    import pandas as pd
    data = pd.read_csv(fn, header=None)
    skids = data[data.columns[skid_column]]
    bundles = get_bundle_from_skid(skids.to_numpy(), project_id=project_id)
    bundles = pd.Series(bundles)
    bundles = bundles[skids]
    assert all(bundles.index == skids)
    data['bundles'] = bundles.values
    if replace_original in [False, 'False', '']:
        out_fn = fn.replace('.csv', '_with_bundles.csv')
    else:
        out_fn = fn
    data.to_csv(out_fn, header=False, index=False)


if __name__ == '__main__':
    l = locals()
    public_functions = [f for f in l if callable(l[f]) and f[0] != '_']
    if len(sys.argv) <= 1 or not sys.argv[1] in public_functions:
        from inspect import signature
        print('Functions available:')
        for f_name in public_functions:
            print('  '+f_name+str(signature(l[f_name])))
            docstring = l[f_name].__doc__
            if not isinstance(docstring, type(None)):
                print(docstring.strip('\n'))
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
