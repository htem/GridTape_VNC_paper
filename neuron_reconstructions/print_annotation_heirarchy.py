#!/usr/bin/env python3

import sys

import pymaid
import pymaid_utils as pu

if len(sys.argv) > 1:
    pu.set_source_project_id(int(sys.argv[1]))

get_annotated = lambda x: pymaid.get_annotated(x, remote_instance=pu.source_project)


def print_annotation_hierarchy(annot, parent_annots=[], indent_level=0):
    prefix = '│  '*(indent_level-1) + '├──'*(indent_level>0)
    annotated = get_annotated([annot] + parent_annots)
    if annotated.empty:
        n_neurons = 0
    else:
        n_neurons = sum(annotated.type == 'neuron')

    txt = prefix + annot
    if n_neurons > 0:
        parent_annots = parent_annots + [annot]
        txt += ' (' + str(n_neurons) + ' neurons)' #+ str(parent_annots)

    subannots = get_annotated([annot])
    if subannots.empty:
        return
    subannots = subannots.loc[subannots.type == 'annotation', 'name']
    if len(subannots) == 0 and n_neurons == 0:
        return
    print(txt)
    subannots = sorted(subannots)
    subannots = sorted(subannots, key=lambda x: x.replace('left ', '').replace('right ',''))
    for subannot in subannots:
        print_annotation_hierarchy(subannot,
                                   parent_annots=parent_annots,
                                   indent_level=indent_level+1)


always_include_annots = []
if pu.source_project.project_id == 59:
    always_include_annots = ['tracing from electron microscopy',
                             '~left-right flipped',
                             '~pruned to nodes with radius 500',
                             '~pruned \(first entry, last exit\) by vol 109']
print_annotation_hierarchy('publication', parent_annots=always_include_annots)
