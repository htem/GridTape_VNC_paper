#!/usr/bin/env python3

import sys
import os
import json

import pymaid
import pymaid_utils as pu

project_folders = {
    2: 'skeletons_in_FANC_space',
    59: 'skeletons_in_JRC2018_VNC_FEMALE_space'
}


def download_neurons(skeletons=True, annotations=True):
    """
    Downloads published neuron reconstructions from a catmaid server as .swc files.
    Currently only works for the Phelps, Hildebrand, Graham et al. 2020 paper,
    but can be generalized when other papers in this dataset come out.

    You must set a global pymaid instance before calling this function.
    """
    project_id = pymaid.utils._eval_remote_instance(None).project_id
    project_folder = project_folders[project_id]

    paper_annot = 'Paper: Phelps, Hildebrand, Graham et al. 2020'
    annotation_exclusions = ['LINKED NEURON', 'need to push updated tracing']

    get_neurons = lambda x: pymaid.find_neurons(
        skids=pymaid.get_skids_by_annotation(x, intersect=True),
    )
    neurons = {}
    neurons['motor_neurons'] = get_neurons([paper_annot, 'motor neuron'])
    neurons['sensory_neurons'] = get_neurons([paper_annot, 'sensory neuron'])
    neurons['other_neurons'] = get_neurons([paper_annot, '~motor neuron', '~sensory neuron'])

    for cell_type in neurons:
        folder = os.path.join(project_folder, cell_type)
        os.makedirs(folder, exist_ok=True)
        n = neurons[cell_type]
        print('Found {} {}'.format(len(n), cell_type))

        if skeletons:
            print('Saving {}'.format(folder))
            n.to_swc(filenames=[os.path.join(folder, name) for name in n.neuron_name])

        if annotations:
            print('Pulling and saving {} annotations'.format(cell_type))
            annotations = [[annot for annot in x if not any([exclude in annot for exclude in annotation_exclusions])]
                           for x in n.annotations]
            annotations_fn = os.path.join(project_folder, cell_type + '_annotations.json')
            with open(annotations_fn, 'w') as f:
                json.dump({a: b for a, b in zip(n.neuron_name, annotations)}, f, indent=4)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        project_ids = [int(x) for x in sys.argv[1:]]
    else:
        project_ids = [pu.source_project.project_id]

    for project in [pu.source_project, pu.target_project]:
        project.make_global()
        download_neurons()
