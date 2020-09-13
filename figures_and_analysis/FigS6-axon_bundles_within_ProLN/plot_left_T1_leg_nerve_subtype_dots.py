#!/usr/bin/env python3

import matplotlib.pyplot as plt

import pymaid
from pymaid import tiles
import pymaid_utils as pu
pu.source_project.make_global()

import bundles

untraced_color = 'black'
unclassified_color = 'lightgreen'
colorword_to_annots = {
    'blue': 'T1 leg motor neuron L1 bundle',
    'matlab6': 'bristle',
    'cyan': 'T1 leg motor neuron L2 bundle',
    'matlab3': 'hair plate',
    'lightblue': 'T1 leg motor neuron L3 bundle',
    'matlab2': 'chordotonal neuron',
    'darkcyan': 'T1 leg motor neuron L4 bundle',
    'matlab4': 'campaniform sensillum',
    'darkblue': 'T1 leg motor neuron L5 bundle',
    unclassified_color: 'T1 leg sensory neuron unclassified subtype',
    'matlab7': 'T1 leg DUM neuron',
    untraced_color: ['possible sensory neuron', 'left T1 leg nerve']
}
colorword_to_nodesize = {
    untraced_color: 50,
    unclassified_color: 100,
    'default': 200
}
default_nodesize = colorword_to_nodesize['default']
colorword_to_label = {
    #untraced_color: 'Putative sensory neuron,\nnot yet reconstructed',
    untraced_color: 'NR',
    #unclassified_color: 'Sensory neuron, unclassified subtype',
    unclassified_color: 'unc',
    'blue': 'L1',
    'cyan': 'L2',
    'lightblue': 'L3',
    'darkcyan': 'L4',
    'darkblue': 'L5',
    'matlab7': 'UM',
    'matlab6': 'br',
    'matlab3': 'hp',
    'matlab2': 'cho',
    'matlab4': 'cs',
}

bbox = [16000, 51000, 424000, 452000, 168300]
job = tiles.TileLoader(bbox, stack_id=10, coords='NM')

job.load_in_memory()

ax = job.render_im(figsize=(20, 20))
for color in colorword_to_annots:
    annots = colorword_to_annots[color]
    node_size = colorword_to_nodesize.get(color, default_nodesize)
    label = colorword_to_label.get(color, annots)  # Default to using the annotations as the label
    skids = pymaid.get_skids_by_annotation(annots, intersect=True)
    job.render_nodes(ax,
                     treenodes=True,
                     connectors=False,
                     skid_include=skids,
                     tn_color=pu.colorword_to_hex[color],
                     tn_kws={'s': node_size, 'label': label})

job.scalebar(size=5000, ax=ax, label=False, pos='upper left', line_kws={'color': 'k', 'lw': 5})

plt.legend(loc='lower left', ncol=6)
save_fn = 'leftT1legNerve_sensoryAndMotorNeuronsColoredBySubtype'
plt.savefig(save_fn + '.png')
print('Saved image to {}'.format(save_fn + '.png'))
plt.savefig(save_fn + '.svg')
print('Saved image to {}'.format(save_fn + '.svg'))
#plt.show()
