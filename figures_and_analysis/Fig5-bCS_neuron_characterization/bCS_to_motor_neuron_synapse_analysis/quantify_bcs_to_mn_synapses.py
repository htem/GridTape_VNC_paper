#!/usr/bin/env python3

import os
import sys
import json
import math

import pandas as pd
import numpy as np
from scipy import stats
from tqdm import tqdm
import matplotlib
#matplotlib.use("TkAgg")
matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import requests
import pymaid
pymaid.set_loggers(30) #Default is 20, INFO. Changed to 30, WARNING, mainly to suppress cached data notices. See https://docs.python.org/3/library/logging.html#levels

sys.path.append('../../../')
import pymaid_utils
pymaid_utils.source_project.make_global()
sys.path.append('../../python_utilities')
import bundles  # GridTape-VNC_repository: figures_and_analysis/python_utilities/bundles.py
import nblast_score_files as nsf  # GridTape-VNC_repository: figures_and_analysis/python_utilities/nblast_score_files.py


#-------DEFAULT VARIABLE DEFINITIONS-------#
#leftT1bcsSkids = [103138, 106558] #Old skeleton IDs for the cut-off fragments of interest
leftT1bcsSkids = [20917, 26820] #skeleton IDs after merging the fragments back in
#rightT1bcsSkids = [115425, 115436] #Old skeleton IDs for the cut-off fragments of interest
rightT1bcsSkids = [79292, 34069] #skeleton IDs after merging the fragments back in

mn_skids_left_T1_all_nerves = set(pymaid.get_skids_by_annotation(['T1 leg motor neuron', 'left soma'], intersect=True))
mn_skids_left_T1_leg_nerve = set(pymaid.get_skids_by_annotation(['T1 leg motor neuron', 'left T1 leg nerve'], intersect=True))
#mn_skids_T1_all_nerves = set(pymaid.get_skids_by_annotation(['T1 leg motor neuron'], intersect=True))

primary_neurite_radius = 500

#treenode_ids for nodes that are being used as a proxy for the location of the spike initiation zone.  Key is MN skid.
#Currently using the last branch point on a motor neuron primary neurite before it heads into the leg nerve.
#last_branch_treenode_ids = {9004: 356706, 2713: 168524, 8991: 70555, 463:
#        4996700, 467: 58104, 9012: 64886, 8995: 67236, 9629: 81068, 9008: 68097}
#These nodes are tagged as "last branch before leaving nerve", so find those points by their tag instead of hardcoding them as above.
skids_to_use_for_spike_initiation_zone_analysis = [9004, 2713, 8991, 463, 467, 9012, 8995, 9629, 9008]  # The leg nerve MNs receiving 5+ bCS synapses
last_branch_treenode_ids = pymaid.find_treenodes(
    tags='last branch before leaving nerve',
    skeleton_ids=skids_to_use_for_spike_initiation_zone_analysis
)
last_branch_treenode_ids.set_index('skeleton_id', inplace=True)
last_branch_treenode_ids = last_branch_treenode_ids['treenode_id']

mn_axon_areas_fn = 'motorNeuronAxonAreas_leftT1legNerve.csv'


#-------FUNCTION DEFINITIONS: HELPERS-------#
def get_bcs_skids(side='left', allow_both=True):
    if side is 'left':
        bcs_skids = leftT1bcsSkids
    elif side is 'right':
        bcs_skids = rightT1bcsSkids
    elif allow_both and side is 'both':
        bcs_skids = leftT1bcsSkids + rightT1bcsSkids
    else:
        raise ValueError('{} is not a valid argument'.format(side))
    return bcs_skids


def get_bcs_fragments(side='left', allow_both=True, fake=False, **kwargs):
    start_points = pymaid.find_treenodes(tags='bCS connectivity analysis start point')
    start_points = {int(node[1].skeleton_id): int(node[1].treenode_id) for node in start_points.iterrows()}
    end_points = pymaid.find_treenodes(tags='bCS connectivity analysis end point')
    end_points = {int(node[1].skeleton_id): int(node[1].treenode_id) for node in end_points.iterrows()}
    if 'skids' in kwargs:  # Allow for custom skids that override the standard bCS skids
        skids = kwargs['skids']
    else:
        if side is 'left':
            skids = leftT1bcsSkids
        elif side is 'right':
            skids = rightT1bcsSkids
        elif allow_both and side is 'both':
            skids = leftT1bcsSkids + rightT1bcsSkids
        else:
            raise ValueError('{} is not a valid argument'.format(side))

    bcs = pymaid.get_neuron(skids)

    if fake:
        return bcs

    for neuron in bcs:
        if int(neuron.skeleton_id) in start_points:
            try:
                neuron.prune_proximal_to(start_points[int(neuron.skeleton_id)])
            except ValueError as e:
                if 'node is root' not in e.args[0]:
                    raise
        if int(neuron.skeleton_id) in end_points:
            neuron.prune_distal_to(end_points[int(neuron.skeleton_id)])
    return bcs


def walk_n_down_primary_neurite(treenode_id, n, nodes=None):
    if nodes is None:
        nodes = pymaid.get_neuron(pymaid.get_skid_from_treenode(treenode_id)[treenode_id]).nodes
    if nodes.index.name != 'treenode_id':
        nodes = nodes.set_index('treenode_id')
    for i in range(n):
        treenode_id = nodes.index[(nodes.parent_id == treenode_id) & (nodes.radius == primary_neurite_radius)]
        if len(treenode_id) is 0:
            raise Exception('Main branch ends before {} steps could be taken!'.format(n))
        if len(treenode_id) > 1:
            raise Exception('Main branch bifurcates! Can\'t handle this case yet')
        treenode_id = treenode_id[0]
    return treenode_id


def import_lT1mn_axon_areas(filename=mn_axon_areas_fn, neuronidcol=0, areacol=1):
    areas_raw = np.genfromtxt(filename, delimiter=',', skip_header=1)[:,[neuronidcol, areacol]]
    #assumes skid = neuronid-1
    areas = {int(neuronid)-1: area for neuronid, area in areas_raw}
    areas_sorted = {skid: areas[skid] for skid in sorted(areas, key=lambda x: areas[x], reverse=True)}
    return areas_sorted


def measure_distance_to_primary_neurite(treenode_id, nodes=None, scale=.001):
    if nodes is None: #If the user has already pulled the nodes table, they can pass it to this function to prevent needing to re-pull the nodes
        nodes = pymaid.get_neuron(pymaid.get_skid_from_treenode(treenode_id)[treenode_id]).nodes.set_index('treenode_id')
    elif nodes.index.name != 'treenode_id':
        nodes = nodes.set_index('treenode_id')
    distance_to_primary_neurite = 0
    while nodes.radius.at[treenode_id] != primary_neurite_radius:
        parent_id = nodes.parent_id.at[treenode_id]
        try:
            distance_to_primary_neurite += np.linalg.norm(nodes.loc[parent_id, ['x', 'y', 'z']] - nodes.loc[treenode_id, ['x', 'y', 'z']])
        except KeyError: #If walking up the tree reached the root before reaching a primary_neurite, return -1 and let the caller decide what to do with it
            return -1, -1
        treenode_id = parent_id
    return distance_to_primary_neurite*scale, treenode_id


#Because root is always upstream, can do a fast walk back to root instead of using dist_to which calls a shortest_path graph function which is presumably slower.
#TODO time this versus pymaid.dist_to
def measure_distance_to_root(treenode_id, nodes=None, scale=.001):
    if nodes is None: #If the user has already pulled the nodes table, they can pass it to this function to prevent needing to re-pull the nodes
        nodes = pymaid.get_neuron(pymaid.get_skid_from_treenode(treenode_id)[treenode_id]).nodes.set_index('treenode_id')
    elif nodes.index.name != 'treenode_id':
        nodes = nodes.set_index('treenode_id')
    distance_to_root = 0
    while nodes.at[treenode_id, 'type'] != 'root':
        parent_id = nodes.parent_id.at[treenode_id]
        #try:
        distance_to_root += np.linalg.norm(nodes.loc[parent_id, ['x', 'y', 'z']] - nodes.loc[treenode_id, ['x', 'y', 'z']])
        #except KeyError: #If walking up the tree reached the root before reaching a primary_neurite, return -1 and let the caller decide what to do with it
        #    return -1
        treenode_id = parent_id

    #return distance_to_root
    return distance_to_root*scale, treenode_id


#-------FUNCTION DEFINITIONS: PULLING DATA-------#
def find_orphans(side='both'):
    """
    Find nodes postsynaptic of a bCS synapse that are tagged as 'orphan'
    """
    connectors = get_bcs_fragments(side=side).presynapses
    postsynaptic_node_info = pymaid.get_connector_details(connectors.connector_id)
    postsynaptic_skids = set([skid for sublist in postsynaptic_node_info.postsynaptic_to for skid in sublist])  # 93
    postsynaptic_annotations = pymaid.get_annotations(postsynaptic_skids)  # 93
    postsynaptic_node_ids = [node_id for sublist in postsynaptic_node_info.postsynaptic_to_node for node_id in sublist] # 471
    postsynaptic_node_tags = pymaid.get_node_tags(postsynaptic_node_ids, node_type='TREENODE')  # 461. Why the drop? 10 duplicates

    #Validation
    tagless_nodes = [i for i in postsynaptic_node_ids if str(i) not in postsynaptic_node_tags]
    assert tagless_nodes == [], ("Some postsynaptic nodes have no tags. Go tag them as"
                                 " 'motor', 'central', or 'orphan': {}".format(tagless_nodes))
    wrongly_tagged_nodes = [i for i, tags in postsynaptic_node_tags.items() if
                            'motor' not in tags and 'orphan' not in tags and 'central' not in tags]
    assert wrongly_tagged_nodes == [], ("Some postsynaptic nodes lack a 'motor', 'central', or"
                                        "'orphan' tag. Go fix this: {}".format(wrongly_tagged_nodes))
    
    orphan_treenode_ids = [treenode_id for treenode_id in postsynaptic_node_ids if 'orphan' in postsynaptic_node_tags[str(treenode_id)]]
    orphan_skids = pymaid.get_skid_from_treenode(orphan_treenode_ids)
    for tid in orphan_treenode_ids:
        if 'orphan' in postsynaptic_annotations[str(orphan_skids[int(tid)])]:
            #print('{} is an orphan'.format(tid))
            pass
        else:
            print('SKELETON ID {} LACKS ORPHAN ANNOTATION BUT HAS ORPHAN NODE {}.'.format(orphan_skids[int(tid)], tid))

    return orphan_treenode_ids


def count_synapse_polyadicity(side='both'):
    connectors = get_bcs_fragments(side=side).presynapses
    connectors['side'] = ['left' if int(skid) in leftT1bcsSkids else 'right' for skid in connectors.skeleton_id]
    connector_details = pymaid.get_connector_details(connectors.connector_id).set_index('connector_id')
    polyadicity = [len(postsynapses) for postsynapses in connector_details.postsynaptic_to_node]
    assert len(connectors) == len(connector_details) and len(connectors) == len(polyadicity)

    print('Total number of T1 bCS synapses analyzed: {}'.format(len(connectors)))
    if side == 'both':
        side_counts = connectors['side'].value_counts()
        print('Number from left T1 bCS neurons: {}'.format(side_counts['left']))
        print('Number from right T1 bCS neurons: {}'.format(side_counts['right']))
    print('The average bCS synapse has {:.2f} ± {:.2f} postsynaptic partners (mean ± sample standard deviation)'.format(np.mean(polyadicity), np.std(polyadicity, ddof=1)))
    print('Total number of postsynaptic neurites receiving input from those {} synapses: {}'.format(len(connectors), sum(polyadicity)))
    #TODO count polyadicity when you only consider postsynaptic motor neurons. Maybe do this here, maybe do this in count_postsynaptic_motor_central_orphan?
    #return polyadicity


def count_motor_connections(side='both', verbose=True):
    """
    Count how many synapses have at least one postsynaptic motor neuron, and
    cross-reference that against whether the synapse is tagged 'motor connection'
    Also warns about monadic synapses, as often that indicates that
    postsynaptic partners were not fully marked.
    """
    connectors = get_bcs_fragments(side=side).presynapses
    connector_tags = pymaid.get_node_tags(connectors.connector_id.values, 'CONNECTOR')
    connector_tags = pd.Series({int(k): v for k, v in connector_tags.items()})
    connector_details = pymaid.get_connector_details(connectors.connector_id).set_index('connector_id')
    connector_details['tags'] = connector_tags
    connector_details.reset_index(inplace=True)


    postsynaptic_skids_and_annotations = pymaid.get_annotations(set([skid for skids in connector_details.postsynaptic_to for skid in skids]))

    motor_connections = 0
    non_motor_connections = 0
    for i in range(len(connector_details)):
        is_motor_connection = False
        if len(connector_details.at[i, 'postsynaptic_to_node']) <= 1:
            #print(connector_details.at[i, 'tags'])
            #print(connector_details.at[i, 'postsynaptic_to_node'])
            if (type(connector_details.at[i, 'tags']) is list and 'monadic' in connector_details.at[i, 'tags']) and len(connector_details.at[i, 'postsynaptic_to_node']) == 1:
                if verbose: print('Connector {} is marked as monadic.'.format(connector_details.at[i, 'connector_id']))
            else:
                if verbose: print('Connector {} only has {} postsynaptic partners. Is reconstruction complete?'.format(connector_details.at[i, 'connector_id'], len(connector_details.at[i,'postsynaptic_to_node'])))
        for skid in connector_details.at[i, 'postsynaptic_to']:
            if 'motor neuron' in postsynaptic_skids_and_annotations[str(skid)]:
                is_motor_connection = True
                break
        if (type(connector_details.at[i,'tags']) is not list or 'motor_connection' not in connector_details.at[i,'tags']) and not is_motor_connection:
            if verbose: print('{} is not a motor connection'.format(connector_details.at[i,'connector_id']))
            non_motor_connections += 1
        elif (type(connector_details.at[i, 'tags']) is list and 'motor connection' in connector_details.at[i,'tags']) and is_motor_connection:
            #print('{} is a motor connection'.format(connector_details.at[i,'connector_id']))
            motor_connections += 1
        else:
            print('Discrepancy for connector {}'.format(connector_details.at[i,'connector_id']))

    print('Out of {} total synapses, {} ({:.2f}%) have at least one motor neuron neurite as a postsynaptic partner'.format(motor_connections + non_motor_connections, motor_connections, motor_connections/(motor_connections+non_motor_connections)*100))


def count_postsynaptic_motor_central_orphan(side='both'):
    connectors = get_bcs_fragments(side=side).presynapses
    connector_details = pymaid.get_connector_details(connectors.connector_id)

    postsynaptic_skids = set([skid for skids in connector_details.postsynaptic_to for skid in skids])
    postsynaptic_nodes = [node for node_list in connector_details.postsynaptic_to_node for node in node_list]  # Single nodes postsynaptic to two synapses are listed twice here
    postsynaptic_nodes_and_skids = try_catch_network_error(
        'pymaid.get_skid_from_treenode(postsynaptic_nodes)',
        variables={'postsynaptic_nodes': postsynaptic_nodes, 'pymaid': pymaid}
    ) #Dict, so no duplicates

    #Validation, only needed to run this once to make sure the above code worked:
    #matches = discrepancies = 0
    #for node in postsynaptic_nodes_and_skids:
    #    if pymaid.get_skid_from_treenode(node)[int(node)] == int(postsynaptic_nodes_and_skids[node]):
    #        matches += 1
    #    else:
    #        discrepancies += 1
    #print(matches,'matches')
    #print(discrepancies,'discrepancies')

    postsynaptic_skids_and_annotations = pymaid.get_annotations(postsynaptic_skids)
    postsynaptic_skids_and_annotations = {int(skid): annots for skid, annots in postsynaptic_skids_and_annotations.items()} #Convert keys from str to int
    if len(postsynaptic_skids_and_annotations) != len(postsynaptic_skids):
        print('These postsynaptic neurons have no annotations:',[skid for skid in postsynaptic_skids if skid not in postsynaptic_skids_and_annotations])

    postsynaptic_nodes_and_tags = pymaid.get_node_tags(postsynaptic_nodes, node_type='TREENODE')
    postsynaptic_nodes_and_tags = {int(node): tags for node, tags in postsynaptic_nodes_and_tags.items()} #Convert keys from str to int
    if len(postsynaptic_nodes_and_tags) != len(set(postsynaptic_nodes)): #'set' needed to remove duplicates
        print('These postsynaptic nodes have no tags:', [node for node in postsynaptic_nodes if node not in postsynaptic_nodes_and_tags])

    orphan_ids = []
    motor_ids = []
    central_ids = []

    # postsynaptic_nodes has nodes listed multiple times if they're
    # postsynaptic to multiple synapses, so iterating through it (instead of
    # through the dict postsynaptic_nodes_and_tags) will count nodes twice if
    # they're postsynaptic to multiple synapses. This is the desired behavior.
    for postsynaptic_node in postsynaptic_nodes:
        try:
            if ('orphan' in postsynaptic_nodes_and_tags[postsynaptic_node] and
                'orphan' in postsynaptic_skids_and_annotations[postsynaptic_nodes_and_skids[postsynaptic_node]]):
                orphan_ids.append(postsynaptic_node)
            elif ('motor' in postsynaptic_nodes_and_tags[postsynaptic_node] and
                  'motor neuron' in postsynaptic_skids_and_annotations[postsynaptic_nodes_and_skids[postsynaptic_node]]):
                motor_ids.append(postsynaptic_node)
            elif ('central' in postsynaptic_nodes_and_tags[postsynaptic_node] and
                  'central neuron' in postsynaptic_skids_and_annotations[postsynaptic_nodes_and_skids[postsynaptic_node]]):
                central_ids.append(postsynaptic_node)
            else:
                print('Tags and/or annotations not in order for postsynaptic node {}'.format(postsynaptic_node))
        except KeyError:
            #This print is redundant with the lists printed above that separately specify which nodes have no tags and which neurons have no annotations.
            print('Node {} has no tags and/or neuron {} has no annotations'.format(postsynaptic_node, postsynaptic_nodes_and_skids[postsynaptic_node]))
            pass

    total_postsynapses = len(motor_ids) + len(central_ids) + len(orphan_ids)
    print('Total postsynaptic neurites:',total_postsynapses)
    print('Postsynaptic neurites that belong to motor neurons:', len(motor_ids), '({:.2f}%)'.format(len(motor_ids)/total_postsynapses*100))
    print('Postsynaptic neurites that belong to central neurons:',len(central_ids), '({:.2f}%)'.format(len(central_ids)/total_postsynapses*100))
    print('Postsynaptic neurites that belong to orphaned fragments:',len(orphan_ids), '({:.2f}%)'.format(len(orphan_ids)/total_postsynapses*100))

    #return orphan_ids, motor_ids, central_ids


def count_T1bCS_to_lT1mn_synapses(side='both', prune_bcs_to_fragments=True, mn_skids='leg nerve', key_type='skid', verbose=False):
    assert key_type in ['skid', 'name']
    assert mn_skids in ['leg nerve', 'all nerves']

    if mn_skids == 'leg nerve':
        mn_skids = mn_skids_left_T1_leg_nerve
    else:
        mn_skids = mn_skids_left_T1_all_nerves

    bcs_skids = get_bcs_skids(side=side)
    if prune_bcs_to_fragments:
        bcs = get_bcs_fragments(side=side)
    else:
        bcs = pymaid.get_neuron(bcs_skids)
    mns = try_catch_network_error('pymaid.get_neuron(mn_skids)',
                                  variables={'pymaid': pymaid, 'mn_skids': mn_skids})
    connectivity = pymaid.adjacency_from_connectors(bcs, mns).astype('uint16')
    connectivity.insert(0, 'total', connectivity.sum(axis=1))
    connectivity = connectivity.T
    connectivity.insert(0, 'total', connectivity.sum(axis=1))
    connectivity.sort_values(by='total', ascending=False, inplace=True)

    if key_type == 'name':
        names = pymaid.get_names(mn_skids)
        connectivity.index = [names[skid] if skid != 'total' else 'total'
                for skid in connectivity.index]
        names = pymaid.get_names(bcs_skids)
        connectivity.columns = [names[skid] if skid != 'total' else 'total'
                for skid in connectivity.columns]

    if verbose:
        s = ('Connectivity matrix - values are the number of synaptic'
             ' connections from one bCS neuron (column label) to one motor'
             ' neuron (row label). Labels are neuron names on CATMAID:')
        print(s)
        print(connectivity)
    return connectivity

def measure_bCS_synapse_to_MN_primary_neurite_distances(side='both', mn_skids='leg nerve'):
    """
    blah
    """
    bcs = get_bcs_fragments(side=side)
    if mn_skids == 'leg nerve':
        mn_skids = mn_skids_left_T1_leg_nerve
    elif mn_skids == 'all_nerves':
        mn_skids = mn_skids_left_T1_all_nerves
    mns = try_catch_network_error('pymaid.get_neuron(mn_skids)',
                                  variables={'pymaid': pymaid, 'mn_skids': mn_skids})

    synapses = bcs.presynapses
    distances = pd.DataFrame()
    for i, synapse in tqdm(synapses.iterrows(), total=len(synapses), desc='Measuring synapse distances'):
        for mn in mns:
            node_coords = mn.nodes.loc[mn.nodes.radius >= primary_neurite_radius, ['x', 'y', 'z']]
            min_dist = (((node_coords - synapse[['x', 'y', 'z']])**2).sum(axis=1)**0.5).min()
            distances.at[mn.skeleton_id, synapse.connector_id] = min_dist

    distances['mean'] = distances.mean(axis=1)
    distances.sort_values(by='mean', inplace=True)
    return distances


def measure_bCS_axon_to_MN_primary_neurite_distances(side='both', mn_skids='leg nerve'):
    """
    Measure the distance between bCS neuron axons and motor neuron primary
    neurites.
    This is the only function in this module that operates on neurons in the
    standard atlas's coordinate space instead of in the EM dataset's space -
    physical distances are compressed a bit by warping to the atlas, and we
    want to perform the measurements in the atlas space.  Because of that, a
    bunch of default variables that work for other functions don't work here,
    and so atlas-project-specific variables are specified here.
    """
    # Get connectivity from the EM-space project since connectors aren't in the
    # atlas project currently. Use key_type=name so we can link to neurons in
    # the atlas project, which have the same name (but different skids)
    connectivity = count_T1bCS_to_lT1mn_synapses(key_type='name') #connMatrixLd

    leftT1bcsSkids = [512068, 510815]  # Atlas-project-specific parameter
    rightT1bcsSkids = [516184, 515577]  # Atlas-project-specific parameter
    if side is 'left':
        bcs_skids = leftT1bcsSkids
    elif side is 'right':
        bcs_skids = rightT1bcsSkids
    elif side is 'both':
        bcs_skids = leftT1bcsSkids + rightT1bcsSkids
    else:
        raise ValueError('{} is not a valid argument'.format(side))

    try:
        pymaid_utils.target_project.make_global()
        mn_skids_left_T1_all_nerves_primary_neurites = pymaid.get_skids_by_annotation(
            ['T1 leg motor neuron', 'left soma',
             'tracing from electron microscopy',
             'pruned to nodes with radius 500',
             '~pruned \(first entry, last exit\) by vol 109'], intersect=True)  # Atlas-project-specific parameter
        mn_skids_left_T1_leg_nerve_primary_neurites = pymaid.get_skids_by_annotation(
            ['T1 leg motor neuron', 'left T1 leg nerve',
             'tracing from electron microscopy',
             'pruned to nodes with radius 500',
             '~pruned \(first entry, last exit\) by vol 109'], intersect=True)  # Atlas-project-specific parameter
        if mn_skids == 'leg nerve':
            mn_skids = mn_skids_left_T1_leg_nerve_primary_neurites
        elif mn_skids == 'all nerves':
            mn_skids = mn_skids_left_T1_all_nerves_primary_neurites

        mns = try_catch_network_error('pymaid.get_neuron(mn_skids)',
                                      variables={'pymaid': pymaid, 'mn_skids': mn_skids})
        bcs = get_bcs_fragments(skids=bcs_skids)
        skid_to_name = pymaid.get_names(mn_skids + bcs_skids)

        overlap = pymaid.cable_overlap(mns, bcs, dist=5).T  # Ld
        overlap.index = [skid_to_name[i].split(' -')[0] for i in overlap.index]
        overlap.columns = [skid_to_name[i].split(' -')[0] for i in overlap.columns]

        overlap.insert(0, 'total', overlap.sum(axis=1))
        overlap = overlap.T
        overlap.insert(0, 'total', overlap.sum(axis=1))
        overlap.sort_values(by='total', ascending=False, inplace=True)

        # Re-order connectivity to have same order as overlap
        connectivity = connectivity.loc[overlap.index]

        plt.figure()
        plt.scatter(overlap['total'].iloc[1:], connectivity['total'][1:])
        plt.show()


        # I don't really like the analysis above. It's fine, but let's try this:
        # Take every synapse marked on the bCS synapse fragments, and calculate
        # the minimum distance to each motor neuron primary neurite. Average
        # those distances for each motor neuron
        synapses = bcs.synapses

        #from scipy.spatial import distance

    finally:
        pymaid_utils.source_project.make_global()



#-------FUNCTION DEFINITIONS: DISTANCE DISTRIBUTIONS-------#

#Want to know how many points on a motor neuron skeleton are a given distance away from the primary neurite,
#to get a sense of the distribution of places that synapses could be made. The approach is to record the
#distances from the primary neurite at which branch points and leaf nodes are found. Then, the number of
#different points on the skeleton at a given distance from the primary neurite is just the number of branches
#closer to the primary neurite than the given distance minus the number of leaf nodes closer than the given distance.
def build_distance_to_primary_neurite_distribution(skid, scale=.001, load_if_exists=True):
    parameter_filename = ('.quantify_bcs_to_mn_synapses_cache/'
                          'distance_to_primary_neurite_distribution_parameters/'
                          'skid {}.json'.format(skid))

    if load_if_exists and os.path.exists(parameter_filename):
        print('Loading parameters from {}'.format(parameter_filename))
        with open(parameter_filename, 'r') as parameter_file:
            distribution_parameters = json.load(parameter_file)
        return {skid: distribution_parameters}

    nodes = pymaid.get_neuron(skid).nodes.set_index('treenode_id')
    distribution_parameters = {"branch_distances": [], "leaf_distances": []}
    branch_ids = nodes.loc[nodes.type == 'branch'].index
    leaf_ids = nodes.loc[(nodes.type == 'end') & (nodes.radius != primary_neurite_radius)].index

    #Here I'm using branch_order to mean number of children minus 1, aka how many more paths there are after the branch than before it
    branch_order = {branch_id: sum(nodes.parent_id == branch_id)-1 for branch_id in branch_ids}
    #TODO find branches for which more than 1 child path is a primary neurite (which occurs only for neurons that go out multiple nerves)

    #This is O(n^2) because for each branch node (of which there are O(n)), it traverses a fraction of the tree (which is O(n)).
    #This could definitely be O(n) if I write a way to get the distance measurements I want using a single full-tree traversal.
    #My guess is that this is the main time sink of this function, so worth doing if I use this code a lot.
    #This takes 3-5 minutes for neuron 2714, so yea, might want to improve this.
    print('Measuring branch distances')
    for branch_id in branch_ids:
        for i in range(branch_order[branch_id]):
            distribution_parameters['branch_distances'].append(measure_distance_to_primary_neurite(branch_id, scale=scale, nodes=nodes)[0])

    print('Measuring leaf distances')
    for leaf_id in leaf_ids:
        dist, primary_neurite_id = measure_distance_to_primary_neurite(leaf_id, scale=scale, nodes=nodes)
        if primary_neurite_id == -1:
            continue
        #dist = measure_distance_to_primary_neurite(leaf_id, scale=scale, nodes=nodes)
        if nodes.at[primary_neurite_id, 'type'] is not 'branch': #TODO check that this works
            print('Leaf node {} is downstream of a non-branching radius {} node. Not counting it as a leaf node.'.format(leaf_id, primary_neurite_radius))
            continue
        distribution_parameters['leaf_distances'].append(measure_distance_to_primary_neurite(leaf_id, scale=scale, nodes=nodes)[0])

    #For the two lines coming out of the soma that aren't downstream of a primary neurite node, I'll get a response of -1.
    #I want to exclude those lines anyway, so just drop the -1 values from the lists.
    distribution_parameters['branch_distances'] = [element for element in distribution_parameters['branch_distances'] if element != -1]
    distribution_parameters['leaf_distances'] = [element for element in distribution_parameters['leaf_distances'] if element != -1]

    #This assertion should catch weird neuron morphologies that I haven't thought about yet
    assert len(distribution_parameters['branch_distances']) == len(distribution_parameters['leaf_distances']), "{} != {}".format(len(distribution_parameters['branch_distances']), len(distribution_parameters['leaf_distances']))

    #This sort takes some time, but saves some time later when evaluating the distribution. Not clear if it saves time overall.
    distribution_parameters['branch_distances'].sort()
    distribution_parameters['leaf_distances'].sort()
    
    #Already taken care of by the scale=scale argument in measure_blah calls above
    #distribution_parameters = scale_distance_distribution(distribution_parameters, scale)

    parent_dir = os.path.dirname(parameter_filename)
    os.makedirs(parent_dir, exist_ok=True)
    with open(parameter_filename, 'w') as parameter_file:
        json.dump(distribution_parameters, parameter_file, indent=4)

    return {skid: distribution_parameters}


def build_distance_to_specified_node_distribution(treenode_id, nodes=None, prune_distal_to=False, prune_nucleus_branches=True, scale=.001, load_if_exists=True):
    skid = pymaid.get_skid_from_treenode(treenode_id)[treenode_id]
    parameter_filename = ('.quantify_bcs_to_mn_synapses_cache/'
                          'distance_to_specified_node_distribution_parameters/'
                          'skid {} treenode {}.json'.format(skid, treenode_id))

    if load_if_exists and os.path.exists(parameter_filename):
        print('Loading parameters from {}'.format(parameter_filename))
        with open(parameter_filename, 'r') as parameter_file:
            distribution_parameters = json.load(parameter_file)
        return {skid: distribution_parameters}

    if nodes is None: 
        #Pull neuron, optionally prune it, reroot it to the specified node, and re-index the nodes DataFrame by the treenode_id column
        neuron = pymaid.get_neuron(skid)
        old_root_id = neuron.root[0]
        if prune_distal_to:
            prune_node = treenode_id
            node_count_before = neuron.n_nodes
            neuron.prune_distal_to(prune_node, inplace=True)
            node_count_after = neuron.n_nodes
            print('Pruned skid {} from {} nodes to {} nodes'.format(skid, node_count_before, node_count_after))
        neuron.reroot(treenode_id, inplace=True)
        if prune_nucleus_branches:
            assert old_root_id == neuron.nodes.treenode_id[neuron.nodes.radius > primary_neurite_radius].iloc[0], 'There\'s a snake in my boot!'
            neuron.prune_distal_to(old_root_id, inplace=True)
        nodes = neuron.nodes.set_index('treenode_id')
        #pymaid.plot3d(neuron)
    elif nodes.index.name != 'treenode_id': #If the user passes nodes, it has to already have been pre-processed as above, except for indexing
        nodes = nodes.set_index('treenode_id')

    distribution_parameters = {"branch_distances": [], "leaf_distances": []}
    branch_ids = nodes.loc[nodes.type == 'branch'].index #Currently takes all 'branch' type nodes. Are there ways to filter weird corner case nodes out here?
    root_id = nodes[nodes.parent_id.isnull()].index.values[0]
    branch_ids = branch_ids.append(pd.Index([root_id])) #The root is also a branch point
    leaf_ids = nodes.loc[(nodes.type == 'end')].index
    #leaf_ids = nodes.loc[(nodes.type == 'end') & (nodes.radius != primary_neurite_radius)].index

    #Here I'm using branch_order to mean number of children minus 1, aka how many more paths there are after the branch than before it
    branch_order = {branch_id: sum(nodes.parent_id == branch_id)-1 for branch_id in branch_ids}
    branch_order[root_id] = sum(nodes.parent_id == root_id)
    #TODO find branches for which more than 1 child path is a primary neurite (which occurs only for neurons that go out multiple nerves)

    #This is O(n^2) because for each branch and leaf node (of which there are O(n)), it traverses a fraction of the tree (which is O(n)).
    #This could definitely be O(n) if I write a way to get the distance measurements I want using a single full-tree traversal.
    #My guess is that this is the main time sink of this function, so would be worth doing if I use this code a lot.
    print('Measuring branch distances')
    for branch_id in branch_ids:
        for i in range(branch_order[branch_id]):
            distribution_parameters['branch_distances'].append(measure_distance_to_root(branch_id, scale=scale, nodes=nodes)[0])

    print('Measuring leaf distances')
    for leaf_id in leaf_ids:
        #dist, primary_neurite_id = measure_distance_to_primary_neurite(leaf_id, scale=scale, nodes=nodes)
        dist = measure_distance_to_primary_neurite(leaf_id, scale=scale, nodes=nodes)
        #TODO check if the primary neurite id is a branch node. if it's not, weird geometry is going on
        distribution_parameters['leaf_distances'].append(measure_distance_to_root(leaf_id, scale=scale, nodes=nodes)[0])

    #distribution_parameters['branch_distances'] = [element for element in distribution_parameters['branch_distances'] if element != -1]
    #distribution_parameters['leaf_distances'] = [element for element in distribution_parameters['leaf_distances'] if element != -1]

    #This assertion should catch weird neuron morphologies that I haven't thought about yet
    assert len(distribution_parameters['branch_distances']) == len(distribution_parameters['leaf_distances']), "{} != {}".format(len(distribution_parameters['branch_distances']), len(distribution_parameters['leaf_distances']))

    #This sort takes some time, but saves some time later when evaluating the distribution. Not clear if it saves time overall.
    distribution_parameters['branch_distances'].sort()
    distribution_parameters['leaf_distances'].sort()

    #distribution_parameters = scale_distance_distribution(distribution_parameters, scale) #Already taken care of by the scale=scale argument in measure_blah calls above

    parent_dir = os.path.dirname(parameter_filename)
    os.makedirs(parent_dir, exist_ok=True)
    with open(parameter_filename, 'w') as parameter_file:
        json.dump(distribution_parameters, parameter_file, indent=4)

    #print({skid: distribution_parameters})
    return {skid: distribution_parameters}


def eval_distance_distribution(distances, distribution_parameters):
    try:
        iterator = iter(distances)
    except TypeError: #If input is a single value (instead of a list), this line makes sure to return a single value (instead of a list)
        return eval_distance_distribution([distances], distribution_parameters)[0]

    distribution_values = []
    for distance in distances:
        num_slabs_at_given_distance = 0

        for branch_distance in distribution_parameters['branch_distances']:
            if branch_distance < distance:
                num_slabs_at_given_distance += 1
            else: #Since the branch_distances are sorted, can break once the value gets higher than distance
                break

        for leaf_distance in distribution_parameters['leaf_distances']:
            if leaf_distance < distance:
                num_slabs_at_given_distance -= 1
            else: #Since the branch_distances are sorted, can break once the value gets higher than distance
                break

        distribution_values.append(num_slabs_at_given_distance)

    return distribution_values


def eval_cumulative_distance_distribution(distances, distribution_parameters):
    try:
        iterator = iter(distances)
    except TypeError: #If input is a single value (instead of a list), this line makes sure to return a single value (instead of a list)
        return eval_distance_distribution([distances], distribution_parameters)[0]

    cumulative_distribution_values = []
    distances = np.append(distances, distribution_parameters['leaf_distances'][-1]) #Make sure to evaluate at the largest leaf distance, which will be used to normalize
    for distance in distances:
        cumulative_distribution_value = 0

        for branch_distance in distribution_parameters['branch_distances']:
            if branch_distance < distance:
                cumulative_distribution_value += distance - branch_distance
            else: #Since the branch_distances are sorted, can break once the value gets higher than distance
                break

        for leaf_distance in distribution_parameters['leaf_distances']:
            if leaf_distance < distance:
                cumulative_distribution_value -= distance - leaf_distance
            else: #Since the branch_distances are sorted, can break once the value gets higher than distance
                break

        cumulative_distribution_values.append(cumulative_distribution_value)

    return [value/cumulative_distribution_values[-1] for value in cumulative_distribution_values[:-1]]


def merge_distance_distributions(distribution_parameters):
    merged_parameters = {'leaf_distances': [], 'branch_distances': []}
    for skid in distribution_parameters:
        merged_parameters['leaf_distances'].extend(distribution_parameters[skid]['leaf_distances'])
        merged_parameters['branch_distances'].extend(distribution_parameters[skid]['branch_distances'])

    merged_parameters['leaf_distances'].sort()
    merged_parameters['branch_distances'].sort()

    return merged_parameters


def integrate_distance_distribution(distribution_parameters):
    return {skid: sum(distribution_parameters[skid]['leaf_distances'])
                  - sum(distribution_parameters[skid]['branch_distances'])
            for skid in distribution_parameters}


def scale_distance_distribution(distribution_parameters, scale):
    if 'leaf_distances' in distribution_parameters:
        return {'branch_distances': [value*scale for value in distribution_parameters['branch_distances']],
                'leaf_distances': [value*scale for value in distribution_parameters['leaf_distances']]}
    else:
        return {skid: {'branch_distances': [value*scale for value in distribution_parameters[skid]['branch_distances']],
                       'leaf_distances': [value*scale for value in distribution_parameters[skid]['leaf_distances']]}
                for skid in distribution_parameters}



#-------FUNCTION DEFINITIONS: PLOTTING-------#
def plot_distance_to_primary_neurite_distribution(skid, title=None, normalize='percentage', ax=None, color='blue'):
    plot_distance_distribution(build_distance_to_primary_neurite_distribution(skid),
                               title=title, normalize=normalize, ax=ax, color=color)


def plot_distance_to_specified_node_distribution(treenode_id, title=None, normalize='percentage', ax=None, color='blue'):
    plot_distance_distribution(build_distance_to_specified_node_distribution(treenode_id),
                               title=title, normalize=normalize, ax=ax, color=color)


xlabel_default = 'Distance from motor neuron\'s primary neurite (µm)'
legend_label_default = 'Synaptic inputs placed\nrandomly onto motor neurons'
def plot_distance_distribution(distribution_parameters,
                               xlabel=xlabel_default, legend_label=legend_label_default,
                               title=None, normalize='cumulative', ax=None, color='blue'):
    assert normalize in ['percentage', 'probability', 'cumulative']

    params = merge_distance_distributions(distribution_parameters)

    xmax = math.ceil(max(params['leaf_distances'])/20)*20
    xvals = np.linspace(0, xmax, 2000)

    #eval on a list walks down the parameters once per xval, so is O(len(params)*len(xvals))
    #Could write a different way to walk down each only once, so O(len(params)+len(xvals))
    #Not clear whether this eval step takes longer than the build step
    #Nope, looks like eval is quite fast
    if normalize == 'cumulative':
        yvals = eval_cumulative_distance_distribution(xvals, params)
    else: #Then normalize is 'percentage' or 'probability'
        yvals = eval_distance_distribution(xvals, params)
        integral = integrate_distance_distribution({'foo': params})['foo']
        yvals = [val/integral for val in yvals]
        if normalize == 'percentage':
            yvals = [val*100 for val in yvals]
    #ymax = math.ceil(max(yvals)/10)*10
    ymax = max(yvals)

    if title is not None:
        plt.title(title)
    if ax is not None:
        ax.plot(xvals, yvals, color=color, label=legend_label)
        ax.set_xlabel(xlabel)
        if normalize == 'cumulative':
            ax.set_ylabel('Cumulative fraction of synaptic input')
        else:
            ax.set_ylabel('% of motor neuron path length per µm', color=color)
        #ax.set_ylabel('# of different skeleton locations', color=color)
        ax.tick_params(axis='y', labelcolor=color)
    else:
        plt.plot(xvals, yvals, label=legend_label)
        plt.xlabel(xlabel)
        if normalize == 'cumulative':
            plt.ylabel('Cumulative fraction of synaptic input')
        else:
            plt.ylabel('% of motor neuron path length per µm', color=color)
        #plt.ylabel('# of different skeleton locations')
    plt.axis([0, xmax, 0, ymax])


def plot_postsynaptic_partners_synapse_counts(side='both', prune_bcs_to_fragments=True,
                                              exclude_orphans=True,
                                              connection_weight_cutoff=2,
                                              connection_weight_indicator_lines=[2, 5, 20]):
    bcs_skids = get_bcs_skids(side=side)
    if prune_bcs_to_fragments:
        bcs = get_bcs_fragments(side=side)
    else:
        bcs = pymaid.get_neuron(bcs_skids)

    synapses = bcs.presynapses
    connector_details = pymaid.get_connector_details(synapses)
    postsynaptic_node_skids = [i for targets_list in connector_details.postsynaptic_to
                        for i in targets_list]
    connection_weights = pd.Series({skid: postsynaptic_node_skids.count(skid)
                                    for skid in set(postsynaptic_node_skids)})
    connection_weights.sort_values(ascending=False, inplace=True)

    skid_to_annots = pymaid.get_annotations(connection_weights.index.to_numpy())
    skid_to_annots = {int(skid): annots for skid, annots in skid_to_annots.items()}
    is_motor = [skid for skid, annots in skid_to_annots.items() if 'motor neuron' in annots]
    is_central = [skid for skid, annots in skid_to_annots.items() if 'central neuron' in annots]
    is_orphan = [skid for skid, annots in skid_to_annots.items() if 'orphan' in annots]
    assert len(is_motor + is_central + is_orphan) == len(connection_weights)

    connections = pd.DataFrame({'weight': connection_weights, 'type': None})
    connections.loc[is_motor, 'type'] = 'motor'
    connections.loc[is_central, 'type'] = 'central'
    connections.loc[is_orphan, 'type'] = 'orphan'
    if exclude_orphans:
        connections = connections.loc[connections.type != 'orphan']

    connections['rank'] = np.arange(len(connections)) + 1

    strong_connections = connections.loc[connections.weight >= connection_weight_cutoff]
    n = len(strong_connections)
    max_weight = max(strong_connections['weight'])

    plt.figure()
    for neuron_type in ['Motor', 'Central'] + ([] if exclude_orphans else ['Orphan']):
        x = strong_connections.loc[strong_connections['type'] == neuron_type.lower(), 'rank']
        y = strong_connections.loc[strong_connections['type'] == neuron_type.lower(), 'weight']
        plt.scatter(x, y, label=neuron_type + ' neuron')
    connection_weight_indicator_lines = [i for i in connection_weight_indicator_lines
                                         if i >= connection_weight_cutoff]
    for weight in connection_weight_indicator_lines:
        plt.plot(range(n + 2), [weight]*(n + 2), 'k--', alpha=0.3)

    plt.xlim([n + 0.5, 0.5])
    xtickgap = 5
    xticks = [1] + list(range(xtickgap, n - int(xtickgap/2), xtickgap)) + [n]
    plt.xticks(xticks)
    ytickgap = 20
    yticks = (([] if any([i <= 2 for i in connection_weight_indicator_lines]) else [0])
              + connection_weight_indicator_lines
              + list(range(ytickgap, max_weight + 1, ytickgap)))
    plt.yticks(yticks, fontsize=8)
    plt.ylim([0, max_weight + 5])
    plt.title('Neurons postsynaptic to\n5 or more T1 bCS synapses', fontsize=8)
    plt.xlabel('Rank (ordered by # of synaptic inputs)', fontsize=8)
    plt.ylabel('# of synaptic inputs\nfrom T1 bCS neurons', fontsize=9)
    plt.legend(fontsize=8)
    plt.gcf().set_size_inches(4, 3)
    plt.tight_layout()

    save_filename = 'neurons_postsynaptic_to_{}_or_more_T1_bCS_synapses'.format(connection_weight_cutoff)
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()


def plot_mn_diameter_vs_bcs_synapse_count(side='both', c='bundles', x_units='area', regress_only_L1=True):
    assert x_units in ['diameter', 'area']

    synapses = count_T1bCS_to_lT1mn_synapses(side=side)['total'].drop('total')
    synapses.index = synapses.index.astype('int')
    areas = import_lT1mn_axon_areas()
    print('Motor neuron axon areas (square microns):', areas)


    skid_to_bundle = bundles.get_bundle_from_skid(
        list(areas.keys()),
        project=pymaid_utils.source_project
    )

    x = []
    y = []
    if regress_only_L1:
        x_L1 = []
        y_L1 = []

    for skid in areas:
        xval = -1
        if x_units == 'diameter':
            xval = (areas[skid]/math.pi)**.5*2
        elif x_units == 'area':
            xval = areas[skid]
        x.append(xval)

        yval = 0
        if skid in synapses:
            yval = synapses[skid]
        y.append(yval)

        if regress_only_L1 and skid_to_bundle[skid] == 'L1':
            x_L1.append(xval)
            y_L1.append(yval)

    if regress_only_L1:
        print('Regressing {} neurons'.format(len(x_L1)))
        slope, intercept, pearsons_r_value, p_value_linregress, std_err = stats.linregress(x_L1, y_L1)
        spearmans_rho, spearmans_p_value = stats.spearmanr(x_L1, y_L1)
    else:
        print('Regressing {} neurons'.format(len(x)))
        slope, intercept, pearsons_r_value, p_value_linregress, std_err = stats.linregress(x, y)
        spearmans_rho, spearmans_p_value = stats.spearmanr(x, y)
    r_value = spearmans_rho
    p_value = spearmans_p_value

    if c is 'bundles':
        c = bundles.get_color(skid_to_bundle.values())

    for bundle in ['L1', 'L2', 'L3', 'L4', 'L5']:
        x_in_bundle = [val for val, skid in zip(x, areas.keys()) if skid_to_bundle[skid] == bundle]
        y_in_bundle = [val for val, skid in zip(y, areas.keys()) if skid_to_bundle[skid] == bundle]
        plt.scatter(x_in_bundle, y_in_bundle, c=bundles.get_color(bundle), label=bundle+' bundle')
    plt.gcf().set_size_inches(5, 4)

    #scatter = plt.scatter(x, y, c=c)
    #handles, labels = scatter.legend_elements(prop='colors')
    #plt.legend(handles, labels)

    x_fit = np.linspace(0, max(x)*1.05, 100)
    plt.plot(x_fit, slope * x_fit + intercept, '--k')
    #plt.plot(x_fit, slope_L1 * x_fit + intercept_L1, '--r')
    #regression_info="Spearman's $\\rho$: %.3f\nSlope: %.2f\nIntercept: %.2f\np-value: %1.e" % (r_value,slope, intercept, p_value)
    regression_info="Spearman's $\\rho$: %.3f\np-value: %1.1e" % (r_value, p_value)
    plt.text(max(x), max(y)/3, regression_info, horizontalalignment='right', verticalalignment='top')
        #verticalalignment='bottom', horizontalalignment='right', transform=ax.transAxes)

    plt.axis([0, max(x)*1.05, -2, max(synapses)*1.05])
    if x_units == 'diameter':
        plt.xlabel('Diameter of motor neuron axon (µm)')
    elif x_units == 'area':
        plt.xlabel(r'Cross-sectional area of motor neuron axon (µm$^2$)', fontsize=10)
    plt.ylabel('# of synapses from T1 bCS neurons')
    plt.title('Motor neuron axon {} is correlated with bCS synapse count'.format(x_units), fontsize=10)
    #plt.title('Motor neuron axon {} vs # of inputs from T1 bCS neurons'.format(x_units))
    #plt.title('L1-bundle motor neurons receive bCS synapses proportional to axon diameter')
    plt.legend(loc='upper left')
    plt.tight_layout()

    save_filename = 'mn_axon_{}_vs_bcs_synapse_count'.format(x_units)
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()
    
    return slope, intercept, r_value, p_value, std_err


def plot_mn_morphological_characteristics_vs_bcs_synapse_counts(regress=True):
    distances = measure_bCS_synapse_to_MN_primary_neurite_distances()
    connectivity = count_T1bCS_to_lT1mn_synapses()
    areas = pd.Series(import_lT1mn_axon_areas())
    areas.index = [str(i) for i in areas.index]  # Ugh I wish I made everything ints

    skid_to_bundle = bundles.get_bundle_from_skid(
        list(areas.index),
        project=pymaid_utils.source_project
    )
    skid_to_bundle = pd.Series(skid_to_bundle)
    skid_to_bundle.index = [str(i) for i in skid_to_bundle.index]
    
    # Re-order all data to put the index in the same order as in distances
    connectivity = connectivity.loc[distances.index]
    areas = areas[distances.index]
    skid_to_bundle = skid_to_bundle[distances.index]
    c = bundles.get_color(skid_to_bundle)

    df = pd.DataFrame({
        'mean_distance': distances['mean']/1000,
        'total_synapses': connectivity['total'],
        'axon_area': areas,
        'bundle': skid_to_bundle,
        'edgecolors': c,
        'facecolors': c})

    gets_zero_synapses = df['total_synapses'] == 0
    zero_synapse_style = 'x'  # choose between 'x' and 'o'

    marker_size_mult = 1.3
    df['marker'] = 'o'
    df['marker_size'] = marker_size_mult * df['total_synapses']

    if zero_synapse_style == 'o':
        df.loc[gets_zero_synapses, 'marker'] = 'o'
        df.loc[gets_zero_synapses, 'facecolors'] = 'none'
        df.loc[gets_zero_synapses, 'marker_size'] = 10
    elif zero_synapse_style == 'x':
        df.loc[gets_zero_synapses, 'marker'] = 'x'
        df.loc[gets_zero_synapses, 'marker_size'] = 15

    plt.figure()
    # The scatter function only lets you plot with a single marker type per
    # function call, so if different marker types are used, call once per type
    for marker in df['marker'].unique():
        marker_matches = df['marker'] == marker
        plt.scatter(df.loc[marker_matches, 'mean_distance'],
                    df.loc[marker_matches, 'axon_area'],
                    marker=marker,
                    s=df.loc[marker_matches, 'marker_size'],
                    edgecolors=df.loc[marker_matches, 'edgecolors'],
                    linewidth=1.3,
                    facecolors=df.loc[marker_matches, 'facecolors'])

    if regress:
        if regress == 'L1':
            is_L1 = df['bundle'] == 'L1'
            regress_x = df.loc[is_L1, 'mean_distance']
            regress_y = df.loc[is_L1, 'axon_area']
            fitline_min_x = regress_x.min()
            fitline_max_x = regress_x.max()
        elif regress == 'connected':
            regress_x = df.loc[~gets_zero_synapses, 'mean_distance']
            regress_y = df.loc[~gets_zero_synapses, 'axon_area']
            fitline_min_x = regress_x.min()
            fitline_max_x = regress_x.max()
        else:
            regress_x = df['mean_distance']
            regress_y = df['axon_area']
            fitline_min_x = 0
            fitline_max_x = 30
        slope, intercept, pearsons_r_value, p_value_linregress, std_err = stats.linregress(
            regress_x,
            regress_y
        )
        spearmans_rho, spearmans_p_value = stats.spearmanr(
            regress_x,
            regress_y
        )
        r_value = spearmans_rho
        p_value = spearmans_p_value
        regression_info = "Spearman's $\\rho$: %.3f\np-value: %1.1e" % (r_value, p_value)
        plt.text(1, 0.05, regression_info, horizontalalignment='left',
                 verticalalignment='bottom', fontsize=8)
        plot_max_x = plt.gca().get_xlim()[1]
        x = np.linspace(fitline_min_x, fitline_max_x, 100)
        plt.plot(x, slope*x+intercept, '--k')
        plt.gca().set_xlim(right=plot_max_x)

    plt.gca().set_xlim(left=0)
    plt.xlabel('Avg. distance from bCS synapses to motor neuron primary neurite (µm)', fontsize=8.5)
    plt.gca().set_ylim(bottom=0)
    plt.ylabel(r'Cross-sectional area of motor neuron axon (µm$^2$)', fontsize=9)

    legend_bundles = bundles.get_bundles_list(nerve='L')
    lines = [Line2D([0], [0], marker='o', color=color, lw=0) for color in bundles.get_color(legend_bundles)]
    #https://matplotlib.org/tutorials/intermediate/legend_guide.html#multiple-legends-on-the-same-axes
    legend = plt.legend(lines, bundles.lengthen(legend_bundles, prefix=''), fontsize=8)
    plt.gca().add_artist(legend)

    if zero_synapse_style == 'o':
        synapse_markers = [Line2D([0], [0], marker='o', lw=0, markersize=10**0.5,
                          markerfacecolor='none', markeredgecolor='k')]
    elif zero_synapse_style == 'x':
        synapse_markers = [Line2D([0], [0], marker='x', lw=0, markersize=15**0.5,
                          markerfacecolor='k', markeredgecolor='k')]
    circle_sizes = [5, 20, 60]
    synapse_markers += [Line2D([0], [0], marker='o', lw=0, markersize=(marker_size_mult*s)**0.5,
                               markerfacecolor='k', markeredgecolor='k')
                        for s in circle_sizes]
    synapse_labels = ['0 synapses'] + [str(s) + ' synapses' for s in circle_sizes]
    plt.legend(synapse_markers, synapse_labels, loc='upper center', fontsize=8)
    plt.gcf().set_size_inches(5, 4)
    plt.tight_layout()

    save_filename = 'mn_morphological_characteristics_vs_bCS_synapse_counts'
    if regress == 'L1':
        save_filename += '_L1regression'
    elif regress == 'connected':
        save_filename += '_connectedTobCSregression'
    elif regress:
        save_filename += '_regression'
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()


lm_neurons = {'21G01': '21G01-LexA_190919_vnc2_neuronL_left',
              '22A08': '22A08-Gal4_190908_F1_C1_left',
              '33C10': '33C10-LexA_190919_vnc1_neuronR_left',
              '35C09': '35C09-Gal4_190819_F2_C2_left',
              '56H01': '56H01-LexA_190919_vnc2_neuronL_left',
              '81A07': '81A07-Gal4_190605_F1_C1_left'}
lm_neuron_labels = {name: 'EM neurons most\nsimilar to '+name for name in lm_neurons}
scores_filename_default = '../../nblast_scores/catmaid_nblast_scores_id79_LMxEM_leftT1_motorNeurons_inNeuropil.csv'
def plot_nblast_score_vs_bcs_synapse_count(side='both',
                                           lm_neurons_to_plot=lm_neurons.keys(),
                                           scores_filename=scores_filename_default,
                                           x_units='rank', only_plot_top_n_ranks=5,
                                           c=None, save_format='svg'):
    try:
        iterator = iter(lm_neurons_to_plot)
    except:
        lm_neurons_to_plot = [lm_neurons_to_plot]

    assert x_units in ['score', 'rank']

    synapses = count_T1bCS_to_lT1mn_synapses(side=side, key_type='name')
    #print('bCS to MN synapses')
    #print(synapses)

    scores = nsf.load_scores(scores_filename, convert_headers_to_names=True)
    scores.index = [s.split(' -')[0] for s in scores.index]
    scores.columns = [s.split(' -')[0] for s in scores.columns]
    #print('MN nblast scores')
    #print(scores)

    x_min = 1e8
    x_max = -1e8
    y_max = 0
    for lm_neuron in lm_neurons_to_plot:
        top_hits = nsf.get_top_hits(scores, lm_neurons[lm_neuron], only_plot_top_n_ranks)
        synapses_received_by_top_hits = synapses.loc[list(top_hits.index), 'total']
        y_max = max(y_max, max(synapses_received_by_top_hits))
        if x_units == 'rank':
            x = range(1, only_plot_top_n_ranks + 1)
        elif x_units == 'score':
            x = scores.loc[lm_neurons[lm_neuron], synapses_received_by_top_hits.index]
        x_min = min(x_min, min(x))
        x_max = max(x_max, max(x))
        plt.scatter(x, synapses_received_by_top_hits, label=lm_neuron_labels[lm_neuron])

    plt.gcf().set_size_inches(4, 4)

    if x_units == 'score':
        plt.axis([x_min-.05*(x_max-x_min), x_max+.05*(x_max-x_min), -1, y_max*1.1])
    elif x_units == 'rank': #Reverse the X axis so rank 1 is on the right
        plt.axis([x_max+.05*(x_max-x_min), x_min-.05*(x_max-x_min), -1, y_max*1.1])
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.xlabel('Similarity {}'.format(x_units))
    plt.ylabel('# of synapses from T1 bCS neurons')
    #plt.title(lm_neurons_to_plot)
    plt.legend(loc='upper left', fontsize=8)
    plt.tight_layout()

    save_filename = 'MN_nblast_{}s_vs_bCS_synapse_counts'.format(x_units)
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()
    #return x_nblast_scores


def plot_T1bCS1_vs_T1bCS2_partners(side='left', mn_skids='leg nerve'): 
    """
    Generate a plot comparing connectivity of the two bCS neurons entering the
    VNC from the same T1 leg. Specify side='left' (default) or side='right' to
    choose which leg's bCS to analyze.
    """
    connectivity = count_T1bCS_to_lT1mn_synapses(side=side, mn_skids=mn_skids)
    connectivity.drop('total', axis=0, inplace=True)
    connectivity.drop('total', axis=1, inplace=True)

    synapse_counts_hashed = [1000*xy[0]+xy[1] for xy in connectivity.to_numpy()]
    synapse_counts_frequency = [[value//1000, value%1000, synapse_counts_hashed.count(value)] for value in set(synapse_counts_hashed)]
    dot_sizes = list(set([a[2] for a in synapse_counts_frequency]))
    dot_sizes.sort()
    for dot_size in dot_sizes:
        synapse_counts_for_dot_size = [a[:2] for a in synapse_counts_frequency if a[2] == dot_size]
        plt.scatter([a[0] for a in synapse_counts_for_dot_size],
                    [a[1] for a in synapse_counts_for_dot_size],
                    s=dot_size*10, label=str(dot_size), c='#a2142f')

    slope, intercept, pearsons_r_value, p_value_linregress, std_err = stats.linregress(connectivity)
    spearmans_rho, spearmans_p_value = stats.spearmanr(connectivity)
    r_value = spearmans_rho
    p_value = spearmans_p_value
    
    #regression_info = "Spearman's $\\rho$: %.3f\nSlope: %.2f\nIntercept: %.2f\np-value: %1.e" % (r_value,slope, intercept, p_value)
    regression_info = "Spearman's $\\rho$: %.3f\np-value: %1.1e" % (r_value, p_value)

    plt.legend(title='# of motor neurons with\nthe given # of synapses', loc='lower right')
    plt.axis('equal')
    plt.gcf().set_size_inches(5, 5)
    if side == 'left':
        x = np.linspace(0,25,100)
    elif side == 'right':
        x = np.linspace(0,15,100)
    plt.plot(x, slope * x + intercept, '--k')
    #plt.text(0, max([count[1] for count in synapse_counts]), regression_info, verticalalignment='top')
    if side == 'left':
        plt.text(0, 20, regression_info, verticalalignment='top')
    else:
        plt.text(0, 12, regression_info, verticalalignment='top') #max([count[1] for count in synapse_counts])
    #plt.plot(x,x, '--k')
    plt.xlabel('# of synapses from {} T1 bCS neuron A'.format(side))
    plt.ylabel('# of synapses from {} T1 bCS neuron B'.format(side))
    plt.tight_layout()

    save_filename = 'T1_bCS_connectivity_comparison_{}A_vs_{}B'.format(side, side)
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()

    #print(synapse_counts_frequency)
    return slope, intercept, r_value, p_value, std_err


def plot_left_vs_right_bCS_partners(mn_skids='leg nerve'):
    """
    Generate a plot comparing connectivity of the two bCS neurons entering the
    VNC from the left T1 leg to the two entering the VNC from the right T1 leg
    """
    connectivity = count_T1bCS_to_lT1mn_synapses(side='both', mn_skids=mn_skids)
    connectivity.drop('total', axis=0, inplace=True)
    connectivity.drop('total', axis=1, inplace=True)
    connectivity['left total'] = connectivity[[str(i) for i in leftT1bcsSkids]].sum(axis=1)
    connectivity['right total'] = connectivity[[str(i) for i in rightT1bcsSkids]].sum(axis=1)
    synapse_counts = connectivity[['left total', 'right total']].to_numpy()

    synapse_counts_hashed = [1000*xy[0]+xy[1] for xy in synapse_counts]
    synapse_counts_frequency = [[value//1000, value%1000, synapse_counts_hashed.count(value)] for value in set(synapse_counts_hashed)]
    #synapse_counts_frequency.append([0,0, len(mn_skids_left_T1_leg_nerve)- len(synapse_counts)])
    dot_sizes = list(set([a[2] for a in synapse_counts_frequency]))
    dot_sizes.sort()
    for dot_size in dot_sizes:
        synapse_counts_for_dot_size = [a[:2] for a in synapse_counts_frequency if a[2] == dot_size]
        plt.scatter([a[0] for a in synapse_counts_for_dot_size],
                    [a[1] for a in synapse_counts_for_dot_size],
                    s=dot_size*8, label=str(dot_size), c='#a2142f')

    slope, intercept, pearsons_r_value, p_value_linregress, std_err = stats.linregress(synapse_counts)
    spearmans_r_value, spearmans_p_value = stats.spearmanr(synapse_counts)
    r_value = spearmans_r_value
    p_value = spearmans_p_value

    #regression_info = "Spearman's $\\rho$: %.3f\nSlope: %.2f\nIntercept: %.2f\np-value: %1.1e" % (r_value,slope, intercept, p_value)
    regression_info = "Spearman's $\\rho$: %.3f\np-value: %1.1e" % (r_value, p_value)

    plt.legend(title='# of motor neurons with\nthe given # of synapses', loc='lower right')
    plt.axis('equal')
    plt.gcf().set_size_inches(6, 4)

    x = np.linspace(0, 42, 100)
    plt.plot(x, slope*x+intercept, '--k')
    plt.text(0, max([count[1] for count in synapse_counts]), regression_info, verticalalignment='top')
    plt.xlabel('# of synapses from left T1 bCS neurons')
    plt.ylabel('# of synapses from right T1 bCS neurons')
    plt.tight_layout()

    save_filename = 'T1_bCS_connectivity_comparison_leftA+B_vs_rightA+B'
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()
    return slope, intercept, r_value, p_value, std_err


def plot_synapse_distance_to_siz(presynaptic_skids='both', postsynaptic_skids=None,
                                 cumulative=True, title=None, ax=None, color='red', load_from_temp=True):
    siz_tids = {skid: walk_n_down_primary_neurite(last_branch_treenode_ids[skid],1) for skid in last_branch_treenode_ids.index}
    if postsynaptic_skids is None:
        postsynaptic_skids = list(siz_tids.keys())
    distance_postsynapse_to_siz = []

    distances_filename = '.quantify_bcs_to_mn_synapses_cache/cached_distances_siz.json'
    if load_from_temp and os.path.exists(distances_filename):
        print('Loading distances from {}'.format(distances_filename))
        with open(distances_filename, 'r') as distances_file:
            distance_postsynapse_to_siz = json.load(distances_file)
        print('Loaded {} postsynapses'.format(len(distance_postsynapse_to_siz)))
    else:
        connectors = get_bcs_fragments(side=presynaptic_skids).presynapses
        #connector_tags = pymaid.get_node_tags(connectors.connector_id.values, 'CONNECTOR')
        #connector_tags = pd.Series({int(k): v for k, v in connector_tags.items()})
        connector_details = pymaid.get_connector_details(connectors.connector_id).set_index('connector_id')
        #connector_details['tags'] = connector_tags
        #postsynaptic_skids_and_annotations = pymaid.get_annotations(set([skid for skids in connector_details.postsynaptic_to for skid in skids]))
        postsynaptic_neurons_nodes = {skid: pymaid.get_neuron(skid).reroot(siz_tids[skid], inplace=False).nodes for skid in postsynaptic_skids}
        for connector_id, details in connector_details.iterrows():
            for postsynaptic_treenode, postsynaptic_skid in zip(details['postsynaptic_to_node'], details['postsynaptic_to']):
                if postsynaptic_skid in postsynaptic_skids:
                    print('Measuring distance from postsynaptic node {}'.format(postsynaptic_treenode))
                    distance_postsynapse_to_siz.append(
                        measure_distance_to_root(
                            postsynaptic_treenode,
                            nodes=postsynaptic_neurons_nodes[postsynaptic_skid]
                        )[0]
                    )
        print('Measured distances of {} postsynapses'.format(len(distance_postsynapse_to_siz)))

    if not os.path.exists(distances_filename):
        with open(distances_filename, 'w') as distances_file:
            json.dump(distance_postsynapse_to_siz, distances_file, indent=4)

    if title is not None:
        plt.title(title)

    if cumulative:
        xvals = np.linspace(0, max(distance_postsynapse_to_siz), 2000)
        total_postsynapse_count = len(distance_postsynapse_to_siz)
        #print('total_postsynapse_count',total_postsynapse_count)
        cumulative_distribution = [np.count_nonzero(distance_postsynapse_to_siz < x)/total_postsynapse_count for x in xvals]

    if ax is not None:
        if cumulative:
            ax.plot(xvals, cumulative_distribution, label='Synaptic inputs from bCS neurons') #, color=color)
            ax.set_ylabel('Cumulative fraction of synaptic inputs') #, color=color)
            ax.set(ylim=[0, 1])
        else:
            ax.hist(distance_postsynapse_to_siz, bins=np.linspace(0,200,101), color=color)
            ax.set_ylabel('# of synapses from T1 bCS neurons', color=color)
            ax.set_yticks([0, 5, 10, 15, 20]) #TODO make this not hardcoded

        #ax.set_xlabel('Distance from postsynaptic location to spike-initation zone (µm)')
        ax.set_xlabel('Distance from motor neuron\'s most distal branch point (µm)')
        ax.tick_params(axis='y', labelcolor=color)
    else:
        if cumulative:
            plt.plot(xvals, cumulative_distribution, label='Synaptic inputs from bCS neurons') #, color=color)
            plt.ylabel('Cumulative fraction of synaptic inputs') #, color=color)
            plt.gca().set(ylim=[0, 1])
        else:
            plt.hist(distance_postsynapse_to_siz, bins=np.linspace(0,200,101))
            plt.ylabel('# of synapses from T1 bCS neurons')
            #plt.xlabel('Distance from postsynaptic location to spike-initation zone (µm)')

        plt.xlabel('Distance from motor neuron\'s most distal branch point (µm)')


def plot_synapse_distance_to_primary_neurite(presynaptic_skids='both', postsynaptic_skids=mn_skids_left_T1_leg_nerve,
                                             cumulative=True, title=None, ax=None, color='red', load_from_temp=True):
    if postsynaptic_skids is None:
        siz_tids = {skid: walk_n_down_primary_neurite(last_branch_treenode_ids[skid],1) for skid in last_branch_treenode_ids.index}
        postsynaptic_skids = list(siz_tids.keys())
    distance_postsynapse_to_primary_neurite = []

    distances_filename = '.quantify_bcs_to_mn_synapses_cache/cached_distances_primaryneurite.json'
    if load_from_temp and os.path.exists(distances_filename):
        print('Loading distances from {}'.format(distances_filename))
        with open(distances_filename, 'r') as distances_file:
            distance_postsynapse_to_primary_neurite = json.load(distances_file)
        print('Loaded {} postsynapses'.format(len(distance_postsynapse_to_primary_neurite)))
    else:
        connectors = get_bcs_fragments(side=presynaptic_skids).presynapses
        connector_details = pymaid.get_connector_details(connectors.connector_id).set_index('connector_id')
        for connector_id, details in connector_details.iterrows():
            for postsynaptic_treenode, postsynaptic_skid in zip(details['postsynaptic_to_node'], details['postsynaptic_to']):
                if postsynaptic_skid in postsynaptic_skids:
                    print('Measuring distance from postsynaptic node {}'.format(postsynaptic_treenode))
                    distance = measure_distance_to_primary_neurite(postsynaptic_treenode)[0]
                    assert distance != -1  # TODO deal with -1 responses better. Probably be like wtf how did that synapse get there.
                    distance_postsynapse_to_primary_neurite.append(distance)
        print('Measured distances of {} postsynapses'.format(len(distance_postsynapse_to_primary_neurite)))

    if not os.path.exists(distances_filename):
        with open(distances_filename, 'w') as distances_file:
            json.dump(distance_postsynapse_to_primary_neurite, distances_file, indent=4)

    if title is not None:
        plt.title(title)

    if cumulative:
        xvals = np.linspace(0, max(distance_postsynapse_to_primary_neurite), 2000)
        total_postsynapse_count = len(distance_postsynapse_to_primary_neurite)
        #print('total_postsynapse_count',total_postsynapse_count)
        cumulative_distribution = [np.count_nonzero(distance_postsynapse_to_primary_neurite < x)/total_postsynapse_count for x in xvals]

    if ax is not None:
        if cumulative:
            ax.plot(xvals, cumulative_distribution, label='Synaptic inputs from bCS neurons') #, color=color)
            ax.set_ylabel('Cumulative fraction of synaptic inputs') #, color=color)
            ax.set(ylim=[0, 1])
        else:
            ax.set_xlabel('Distance from motor neuron\'s primary neurite (µm)')
            ax.set_ylabel('# of synapses from T1 bCS neurons', color=color)
            ax.hist(distance_postsynapse_to_primary_neurite, bins=np.linspace(0,100,51), label='Synaptic inputs from bCS neurons', color=color)
            ax.tick_params(axis='y', labelcolor=color)
    else:
        if cumulative:
            plt.plot(xvals, cumulative_distribution, label='Synaptic inputs from bCS neurons') #, color=color)
            plt.ylabel('Cumulative fraction of synaptic inputs') #, color=color)
            plt.gca().set(ylim=[0, 1])
        else:
            plt.xlabel('Distance from motor neuron\'s primary neurite (µm)')
            plt.ylabel('# of synapses from T1 bCS neurons')
            plt.hist(distance_postsynapse_to_primary_neurite, bins=np.linspace(0,10,51), color=color)


def plot_overlaid_synapses_and_distance_distributions(plot_to_primary_neurite=True,
                                                      plot_to_last_branch=False,
                                                      cumulative=True):
    all_siz_distributions = {}
    all_primary_neurite_distributions = {}
    siz_tids = {skid: walk_n_down_primary_neurite(last_branch_treenode_ids[skid],1) for skid in last_branch_treenode_ids.index}
    for skid in siz_tids:
        if plot_to_last_branch:
            siz_distrib = build_distance_to_specified_node_distribution(siz_tids[skid], prune_distal_to=True)
            all_siz_distributions.update(siz_distrib)
        if plot_to_primary_neurite:
            mb_distrib = build_distance_to_primary_neurite_distribution(skid)
            all_primary_neurite_distributions.update(mb_distrib)

    if cumulative:
        if plot_to_last_branch:
            plt.subplots()
            plot_synapse_distance_to_siz(presynaptic_skids='both',
                                         postsynaptic_skids=list(siz_tids.keys()),
                                         cumulative=cumulative, color='black')
            plot_distance_distribution(all_siz_distributions,
                                       xlabel='Distance from motor neuron\'s most distal branch point (µm)',
                                       normalize='cumulative', color='black')
            plt.legend()
            plt.gcf().set_size_inches(5, 4)
            plt.tight_layout()

        if plot_to_primary_neurite:
            plt.subplots()
            plot_synapse_distance_to_primary_neurite(presynaptic_skids='both',
                                                     postsynaptic_skids=list(siz_tids.keys()),
                                                     cumulative=cumulative,  color='black')
            plot_distance_distribution(all_primary_neurite_distributions, normalize='cumulative', color='black')
            plt.legend()
            plt.gcf().set_size_inches(5, 4)
            plt.tight_layout()
    else:
        #https://matplotlib.org/gallery/api/two_scales.html
        if plot_to_last_branch:
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()

            plot_synapse_distance_to_siz(presynaptic_skids='both',
                                         postsynaptic_skids=list(siz_tids.keys()),
                                         cumulative=cumulative, ax=ax1)
            plot_distance_distribution(all_siz_distributions,
                                       xlabel='Distance from motor neuron\'s most distal branch point (µm)',
                                       normalize='percentage', ax=ax2)
            fig.tight_layout()
        if plot_to_primary_neurite:
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()
            plot_synapse_distance_to_primary_neurite(presynaptic_skids='both',
                                                     postsynaptic_skids=list(siz_tids.keys()),
                                                     cumulative=cumulative, ax=ax1)
            plot_distance_distribution(all_primary_neurite_distributions, normalize='percentage', ax=ax2)
            fig.tight_layout()

    save_filename = 'location_of_bCS_synapses_onto_MNs'
    plt.savefig(save_filename + '.svg', transparent=True)
    plt.savefig(save_filename + '.png', transparent=False)
    plt.show()


def plot_each_motor_neurons_synapse_distribution(plot_to_siz=True, plot_to_primary_neurite=True):
    siz_tids = {skid: walk_n_down_primary_neurite(last_branch_treenode_ids[skid],1) for skid in last_branch_treenode_ids.index}
    for skid in siz_tids:
        if plot_to_siz:
            print('Building distance distribution')
            distribution_params = build_distance_to_specified_node_distribution(siz_tids[skid], prune_distal_to=True)
            print('Plotting distance distribution')
            plot_distance_distribution(distribution_params)
            plot_synapse_distance_to_siz(presynaptic_skids='both', postsynaptic_skids=[skid])
            plt.title('Distance from spike-initiation zone for skid {}'.format(skid))
            plt.show()
        if plot_to_primary_neurite:
            print('Building distance distribution for {}'.format(skid))
            distribution_params = build_distance_to_primary_neurite_distribution(skid)
            print('Plotting distance distribution')
            plot_distance_distribution(distribution_params)
            plot_synapse_distance_to_primary_neurite(presynaptic_skids='both', postsynaptic_skids=[skid])
            plt.title('Distance from primary neurite for skid {}'.format(skid))
            plt.show()


# -- UTILS -- #
def prompt(m):
    response = input(m + ' [y/n] ')
    if response.lower() == 'y':
        return True
    elif response.lower() == 'n':
        return False
    else:
        print('Response not understood, assuming n')
        return False

def try_catch_network_error(code, max_tries=5, variables=None):
    success = False
    tries = 1
    while not success and tries < max_tries:
        try:
            ret = eval(code, variables)
        except requests.exceptions.ConnectionError:
            print('Network error on try {}, retrying...'.format(tries))
            tries += 1
        else:
            success = True

    if not success: #Last try, don't catch exception
        ret = eval(code, variables)

    return ret


#-------MAIN CODE BODY-------#
def main():
    print('')
    force_yes = False
    if len(sys.argv) > 1:
        force_yes = sys.argv[1] == 'yes'

    if force_yes or prompt('Want to see summary statistics for bCS -> MN connectivity?'):
        count_synapse_polyadicity()
        print('')
        count_motor_connections(verbose=False)
        print('')
        count_postsynaptic_motor_central_orphan()
        print('')
        count_T1bCS_to_lT1mn_synapses(key_type='name', verbose=True)
        print('')

    if force_yes or prompt('Want to see how many times bCS neurons synapse onto their postsynaptic targets?'):
        plot_postsynaptic_partners_synapse_counts() #connection_weight_cutoff=5)

    if force_yes or prompt('Want to plot how far away bCS -> MN synapses are from the MN primary neurite?'):
        plot_overlaid_synapses_and_distance_distributions(cumulative=True)

    if force_yes or prompt('Want to compare connectivity of the two left T1 bCS neurons?'):
        plot_T1bCS1_vs_T1bCS2_partners(side='left')
    if force_yes or prompt('Want to compare connectivity of the two right T1 bCS neurons?'):
        plot_T1bCS1_vs_T1bCS2_partners(side='right')
    if force_yes or prompt('Want to compare connectivity of the two left T1 bCS vs the two right T1 bCS?'):
        plot_left_vs_right_bCS_partners()

    #if force_yes or prompt('Want to compare motor neuron axon thickness vs number of inputs from bCS?'):
        #plot_mn_diameter_vs_bcs_synapse_count(side='both', c='bundles', x_units='area')
    if force_yes or prompt('Want to compare motor neuron morphological characteristics to number of inputs from bCS?'):
        plot_mn_morphological_characteristics_vs_bcs_synapse_counts(regress=True)

    #if force_yes or prompt('Want to look at bCS inputs to 81A07 and 35C09 hits?'):
    #    x_units = 'rank'  #'score'
    #    plot_nblast_score_vs_bcs_synapse_count(lm_neurons_to_plot=['81A07', '35C09'], x_units=x_units)

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError('Network connection error. Try rerunning this script and hope for better luck.')
