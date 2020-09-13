#!/usr/bin/env python3

import os
import json
import pymaid_utils as pu
pu.set_source_project_id(2)

def combine_jsons(in_fn1, in_fn2, out_fn):
    with open(in_fn1) as in_f1:
        data = json.load(in_f1)
    with open(in_fn2) as in_f2:
        data.extend(json.load(in_f2))
    with open(out_fn, 'w') as out_f:
        json.dump(data, out_f, indent=1)

# --- Fig 3 --- #
fn1 = pu.makejson_motorneurons()
fn2 = pu.makejson_sensoryneurons()
combine_jsons(fn1, fn2, fn1.replace('motor', 'sensoryAndMotor'))

# --- Fig 4 --- #
fn = pu.makejson_leftT1SN_types()
os.rename(fn, fn.replace('.json', '_withUnclassifieds.json'))
pu.makejson_leftT1SN_types(show_unclassified=False)

fn = pu.makejson_chordotonal_subtypes()
os.rename(fn, fn.replace('.json', '_withUnclassifieds.json'))
pu.makejson_chordotonal_subtypes(show_unclassified=False)

pu.makejson_leftT1hairplates()

# --- Fig 5 --- #
pu.makejson_bCS()
pu.makejson_T1bCS_near_lProLN_MNs()


# --- Fig 6 --- #
fn = pu.makejson_T1mn_bundles(soma_side='left')
os.rename(fn, fn.replace('.json', '_L.json'))
fn = pu.makejson_T1mn_bundles(soma_side='right')
os.rename(fn, fn.replace('.json', '_R.json'))
fn = pu.makejson_T1mn_bundles()
os.rename(fn, fn.replace('.json', '_L+R.json'))

# --- Fig S2 --- #
pu.make_json_by_annotations(
    {
        'matlab1': ['peripherally synapsing interneuron', 'left soma'],
        'matlab7': ['peripherally synapsing interneuron', 'right soma']
    },
    'peripherallySynapsingInterneurons'
)

pu.write_catmaid_json(
    {
        9771: pu.colorword_to_hex['matlab1'],
        9872: pu.colorword_to_hex['matlab6'],
        11439: pu.colorword_to_hex['matlab2'],
        11697: pu.colorword_to_hex['matlab3']
    },
    'project2_T1multinerveNeurons.json'
)

pu.makejson_DUMs(include_ag=False)


# --- Fig S5 --- #
pu.make_rainbow_json_by_position(
    'receives 2\+ total synapses in left T1 from left or right T1 bCS',
    'project2_central_neurons_postsynaptic_to_bCS_2plus_synapses',
    extract_position='root_y'
)
pu.make_rainbow_json_by_position(
    'receives 5\+ total synapses in left T1 from left or right T1 bCS',
    'project2_central_neurons_postsynaptic_to_bCS_5plus_synapses',
    extract_position='root_x',
    convert_values_to_rank=True,
    #colormap=list(pu.turbo_colormap_data[30:90])+list(pu.turbo_colormap_data[-80:-10])
    colormap=list(pu.turbo_colormap_data[-10:-80:-1])+list(pu.turbo_colormap_data[90:30:-1])
)

# --- Fig S7 --- #
pu.make_json_by_annotations(
    {
        'matlab6': ['T1 leg motor neuron L5 bundle', 'left soma'],
        'matlab4': ['T1 leg motor neuron L5 bundle', 'right soma']
    },
    'T1legMNsL5bundle'
)

