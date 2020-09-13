#!/usr/bin/env python3

import os
import json
import pymaid_utils as pu
pu.set_source_project_id(59)

def combine_jsons(in_fn1, in_fn2, out_fn):
    with open(in_fn1) as in_f1:
        data = json.load(in_f1)
    with open(in_fn2) as in_f2:
        data.extend(json.load(in_f2))
    with open(out_fn, 'w') as out_f:
        json.dump(data, out_f, indent=1)

# --- Fig 3 --- #
fn1 = pu.makejson_motorneurons(kind='EM',
                               radius_pruned=False,
                               volume_pruned=False,
                               flipped=False)
fn2 = pu.makejson_sensoryneurons(kind='EM', flipped=False)
combine_jsons(fn1, fn2, fn1.replace('motor', 'sensoryAndMotor'))

# --- Fig 4 --- #
fn = pu.makejson_leftT1SN_types(kind='EM')
os.rename(fn, fn.replace('.json', '_withUnclassifieds.json'))
pu.makejson_leftT1SN_types(kind='EM', show_unclassified=False)

fn = pu.makejson_chordotonal_subtypes(kind='EM')
os.rename(fn, fn.replace('.json', '_withUnclassifieds.json'))
pu.makejson_chordotonal_subtypes(kind='EM', show_unclassified=False)

pu.makejson_leftT1hairplates(kind='EM')

# --- Fig 5 --- #
pu.makejson_bCS(kind='EM', flipped=False)
pu.makejson_T1bCS_near_lProLN_MNs(kind='EM',
                         radius_pruned=True,
                         volume_pruned=False,
                         flipped=False)

# --- Fig 6 --- #
#Unpruned
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='left',
                              radius_pruned=False,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='right',
                              radius_pruned=False,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_R.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              radius_pruned=False,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L+R.json'))
#Pruned to primary neurite
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='left',
                              radius_pruned=True,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L_primaryNeurites.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='right',
                              radius_pruned=True,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_R_primaryNeurites.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              radius_pruned=True,
                              volume_pruned=False,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L+R_primaryNeurites.json'))
#Pruned to neuropil
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='left',
                              radius_pruned=False,
                              volume_pruned=True,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L_inNeuropil.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='right',
                              radius_pruned=False,
                              volume_pruned=True,
                              flipped=True)
os.rename(fn, fn.replace('.json', '_flippedR_inNeuropil.json'))
combine_jsons(fn.replace('.json', '_L_inNeuropil.json'),
              fn.replace('.json', '_flippedR_inNeuropil.json'),
              fn.replace('.json', '_L+flippedR_inNeuropil.json'))
#Pruned to primary neurites and pruned to neuropil
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='left',
                              radius_pruned=True,
                              volume_pruned=True,
                              flipped=False)
os.rename(fn, fn.replace('.json', '_L_primaryNeurites_inNeuropil.json'))
fn = pu.makejson_T1mn_bundles(kind='EM',
                              soma_side='right',
                              radius_pruned=True,
                              volume_pruned=True,
                              flipped=True)
os.rename(fn, fn.replace('.json', '_flippedR_primaryNeurites_inNeuropil.json'))
combine_jsons(fn.replace('.json',  '_L_primaryNeurites_inNeuropil.json'),
              fn.replace('.json', '_flippedR_primaryNeurites_inNeuropil.json'),
              fn.replace('.json', '_L+flippedR_primaryNeurites_inNeuropil.json'))

# --- Fig S2 --- #
pu.write_catmaid_json(
    {
        512894: pu.colorword_to_hex['matlab1'],
        511695: pu.colorword_to_hex['matlab7']
    },
    'project59_EM_peripherallySynapsingInterneurons.json'
)

pu.write_catmaid_json(
    {
        516721: pu.colorword_to_hex['matlab1'],
        517296: pu.colorword_to_hex['matlab6'],
        515119: pu.colorword_to_hex['matlab2'],
        516098: pu.colorword_to_hex['matlab3']
    },
    'project59_EM_T1multinerveNeurons.json'
)

pu.makejson_DUMs(kind='EM', include_ag=False, flipped=False)


# --- Fig S5 --- #
pu.make_rainbow_json_by_position(
    'receives 2\+ total synapses in left T1 from left or right T1 bCS',
    'project59_EM_central_neurons_postsynaptic_to_bCS_2plus_synapses',
    extract_position='root_y'
)
pu.make_rainbow_json_by_position(
    'receives 5\+ total synapses in left T1 from left or right T1 bCS',
    'project59_EM_central_neurons_postsynaptic_to_bCS_5plus_synapses',
    extract_position='root_x',
    convert_values_to_rank=True,
    colormap=list(pu.turbo_colormap_data[30:90])+list(pu.turbo_colormap_data[-80:-10])
)

# --- Fig S7 --- #
pu.write_catmaid_json(
    {
        497473: pu.colorword_to_hex['matlab6'],
        520479: pu.colorword_to_hex['matlab4']
    },
    'project59_EM_T1legMNsL5bundle_L+flippedR.json'
)

