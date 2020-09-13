#!/usr/bin/env python3
# Utilities for working with nblast csv files exported from catmaid

import sys

import numpy as np
import pandas as pd
import requests

default_catmaid_project_id = 59

def load_scores(filename, convert_headers_to_names=False, **kwargs):
    scores = pd.read_csv(filename, index_col=0)

    try: scores.columns = pd.to_numeric(scores.columns)
    except: pass

    try: scores.index = pd.to_numeric(scores.index)
    except: pass

    if convert_headers_to_names:
        reheader_as_names(scores, inplace=True, **kwargs)

    return scores


def write_scores(scores, filename):
    scores.to_csv(filename)


def pull_neuron_info(scores, pull_annotations=True, project_id=None):
    """
    Given a nblast score csv file with row and column headers that refer
    to neurons, pull those neurons' names, skeleton ids, and annotations
    from catmaid and return them.
    Arguments:
        scores -- name of a scores csv file OR a scores DataFrame.
        project_id -- project id from which to pull info. Defaults to 59.
    Returns a 4-tuple containing:
        1. A string, either 'names' or 'skids', to indicate whether the
           headers were found to be neuron names or neuron skeleton IDs.
        2. A dict, whose keys are names and values are skids.
        3. A dict, whose keys are skids and values are names.
        4. A dict, whose keys are skids and values are the list of
           annotations on that neuron.

    Example call:
    (headers_are, name_to_skid, skid_to_name,
        skid_to_annots) = pull_neuron_info('scores.csv')
    """
    if isinstance(scores, str):
        scores = load_scores(scores)

    import pymaid
    import pymaid_utils as pu
    temp_pid = pu.source_project.project_id
    if project_id is None:
        project_id = default_catmaid_project_id
        print(f'Defaulting to using project id {project_id}')
    else:
        project_id = int(project_id)
    pu.set_source_project_id(project_id)

    print('Linking names and skeleton IDs...')
    try:
        headers_are = 'names'
        em_names = scores.index
        lm_names = scores.columns
        em_ids = pymaid.get_skids_by_name(em_names,
            remote_instance=pu.source_project)
        lm_ids = pymaid.get_skids_by_name(lm_names,
            remote_instance=pu.source_project)

        ids = pd.concat([em_ids, lm_ids])

        name_to_skid = {i[1][0] : i[1][1] for i in ids.iterrows()}
        skid_to_name = {i[1][1] : i[1][0] for i in ids.iterrows()}
    except requests.exceptions.ConnectionError:
        raise
    except Exception as e:
        if e.args != ('No matching name(s) found',):
            raise
        headers_are = 'skids'
        em_skids = scores.index.values
        lm_skids = scores.columns.values
        skid_to_name = pymaid.get_names(em_skids,
            remote_instance=pu.source_project)
        em_names = list(skid_to_name.values())
        skid_to_name.update(pymaid.get_names(lm_skids,
            remote_instance=pu.source_project))
        if len(skid_to_name) == 0:
            raise ValueError('Row and column headers could not be interpreted as'
                             ' skeleton ids or neuron names.')
        skid_to_name = {int(k): v for k, v in skid_to_name.items()}
        name_to_skid = {v: k for k, v in skid_to_name.items()}

    if not pull_annotations:
        pu.source_project.project_id = temp_pid
        return (headers_are, name_to_skid, skid_to_name, None)

    print('Pulling annotations... (This may take a minute)')
    skid_to_annots = pymaid.get_annotations(list(name_to_skid.keys()),
        remote_instance=pu.source_project)
    skid_to_annots = {int(k): v for k, v in skid_to_annots.items()}

    pu.source_project.project_id = temp_pid
    return (headers_are, name_to_skid, skid_to_name, skid_to_annots)


def get_top_hits(scores, neuron_id, n_hits=0, partial_match=True):
    """
    Return a sorted list of the scores for the requested neuron.
    If n_hits=0, scores are returned for all searched neurons.
    Otherwise the top int(n_hits) scores are returned
    """
    if isinstance(scores, str):
        scores = load_scores(scores)

    if scores.index.dtype == np.dtype('O') and isinstance(neuron_id, int):
        raise ValueError('Scores headers are neuron names but neuron_id was'
                         ' given as an integer.')
    if scores.index.dtype == np.dtype('int64') and isinstance(neuron_id, str):
        raise ValueError('Scores headers are skeleton IDs but neuron_id was'
                         ' given as a neuron name.')

    if partial_match:
        matching_rows = [str(neuron_id) in str(idx) for idx in scores.index]
        matching_cols = [str(neuron_id) in str(col) for col in scores.columns]
        if matching_rows.count(True) + matching_cols.count(True) > 1:
            s = "Identifier {} found multiple times in scores' rows or columns".format(neuron_id)
            raise Exception(s)
        elif matching_rows.count(True) + matching_cols.count(True) == 0:
            s = "Identifier {} not found in scores' rows or columns".format(neuron_id)
            raise Exception(s)
        if matching_rows.count(True) == 1:
            neuron_id = scores.index[matching_rows][0]
            hits = scores.loc[neuron_id, :]
        elif matching_cols.count(True) == 1:
            neuron_id = scores.columns[matching_cols][0]
            hits = scores.loc[:, neuron_id]
    else:
        if neuron_id in scores.index:
            hits = scores.loc[neuron_id, :]
        elif neuron_id in scores.columns:
            hits = scores.loc[:, neuron_id]
        else:
            #hits = "Identifier {} not found in scores' rows or columns".format(neuron_id)
            s = "Identifier {} not found in scores' rows or columns".format(neuron_id)
            raise Exception(s)

    hits = hits.sort_values(ascending=False)
    if n_hits == 0:
        return hits
    else:
        return hits[:n_hits]


def reheader_as_names(scores,
                      inplace=False, 
                      remove_extensions=True,
                      remove_spaces=False,
                      write_reheadered_scores=False,
                      write_header_map=False,
                      write_fn=None,
                      project_id=None):
    """
    Given a csv file of NBLAST results downloaded from CATMAID,
    replace the row and column titles from skeleton IDs to neuron names.
    """
    import pymaid
    import pymaid_utils as pu
    if project_id is None:
        project_id = default_catmaid_project_id
        print(f'Defaulting to using project id {project_id}')
    else:
        project_id = int(project_id)
    pu.set_source_project_id(project_id)
    pu.source_project.make_global()

    def format_name(name,
                    remove_extensions=remove_extensions,
                    remove_spaces=remove_spaces):
        if remove_extensions:
            name = name.split(' -')[0]
        if remove_spaces:
            name = name.replace(' ', '_')
        return name

    if isinstance(scores, str):
        write_reheadered_scores = True
        write_header_map = True
        write_fn = scores
        scores = load_scores(scores)

    if write_header_map:
        assert write_fn is not None, 'write_fn must be set in order to write to file'
        assert write_fn.endswith('.csv')

    _, _, skid_to_name, _ = pull_neuron_info(scores, pull_annotations=False)
    skid_to_name = {skid: format_name(name) for skid, name in skid_to_name.items()}

    if write_fn is not None:
        with open(write_fn.replace('.csv','.row_info.csv'), 'w') as out_f:
            for skid in scores.index:
                out_f.write('{},{}\n'.format(skid, format_name(skid_to_name[skid])))
        with open(write_fn.replace('.csv','.col_info.csv'), 'w') as out_f:
            for skid in scores.columns:
                out_f.write('{},{}\n'.format(skid, format_name(skid_to_name[skid])))

    if inplace:
        scores.rename(index=skid_to_name, columns=skid_to_name, inplace=True)
    else:
        scores = scores.rename(index=skid_to_name, columns=skid_to_name, inplace=False)
    if write_reheadered_scores:
        write_scores(scores, write_fn.replace('.csv', '_headers_as_names.csv'))
    if not inplace:
        return scores


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
