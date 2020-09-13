#!/usr/bin/env python3

import sys

import numpy as np
np.set_printoptions(suppress=True)
import pandas as pd
from matplotlib import pyplot as plt
import scipy.cluster.hierarchy

sys.path.append('../../../python_utilities')
import nblast_score_files as nsf
import bundles


#Pick one:
cluster_by = 'primaryNeurites'
#cluster_by = 'neuritesWithinNeuropil'

#Pick a default:
side = 'left'
#side = 'right'
#side = 'both'

#Pick a default:
#label_by = 'names'
label_by = 'bundles'
#label_by = 'both'

label_with_bcs_synapse_count = False

config = {
    'left': {
        'primaryNeurites': {
            'score filename': '../nblast_scores/catmaid_nblast_scores_id86_T1motorNeurons_primaryNeuritesInNeuropil_left.csv',
            'v3.1 score filename': '../nblast_scores/catmaid_nblast_scores_id72_T1motorNeurons_primaryNeuritesInNeuropil_left.csv',
            'v2 score filename': 'L_T1_MNs_primaryNeurites_47.csv',
            'linkage_method': 'single',
            'color_threshs': {
                'L': 0.4,
                'A': 0.4,
                'V': 0.3,
                'D': 0.5
            },
            'optimal_ordering': {
                'L': True,
                'A': False,
                'V': True,
                'D': True,
                'all': True
            }
        }
    },
    'right': {
        'primaryNeurites': {
            'score filename': '../nblast_scores/catmaid_nblast_scores_id87_T1motorNeurons_primaryNeuritesInNeuropil_right.csv',
            'v3.1 score filename': '../nblast_scores/catmaid_nblast_scores_id73_T1motorNeurons_primaryNeuritesInNeuropil_right.csv',
            'v2 score filename': 'R_T1_MNs_primaryNeurites_48.csv',
            'linkage_method': 'single',
            'color_threshs': {
                'L': 0.413,
                'A': 0.25,
                'V': 0.3,
                'D': 0.7
            },
            'optimal_ordering': {
                'L': True,
                'A': False,
                'V': False,
                'D': True,
                'all': True
            }
        }
    },
    'both': {
        'primaryNeurites': {
            'score filename': '../nblast_scores/catmaid_nblast_scores_id88_T1motorNeurons_primaryNeuritesInNeuropil_leftAndFlippedRight.csv',
            'v3.1 score filename': '../nblast_scores/catmaid_nblast_scores_id69_T1motorNeurons_primaryNeuritesInNeuropil_leftAndFlippedRight.csv',
            'v2 score filename': 'L+flippedR_T1_MNs_primaryNeurites_46.csv',
            'linkage_method': 'single'
        },
        'neuritesWithinNeuropil': {
            'score filename': '',
            'v3.1 score filename': '../nblast_scores/catmaid_nblast_scores_id70_T1motorNeurons_allNeuritesInNeuropil_leftAndFlippedRight.csv',
            'v2 score filename': 'L+flippedR_T1_MNs_pruned_44.csv',
            'linkage_method': 'ward'
        }
    }
}


def get_labels(side=side, label_by=label_by):
    filename = config[side][cluster_by]['score filename']

    with open(filename.replace('.csv', '.asNames.csv'), 'r') as f:
        labels_by_names = [label.strip('"') for label in f.readline().strip().split(',')]
        labels_by_names = [label.replace(' (flipped)','') for label in labels_by_names]
    del labels_by_names[0]

    with open(filename.replace('.csv', '.asBundles.csv'), 'r') as f:
        labels_by_bundles = [label.strip('"') for label in f.readline().strip().split(',')]
    del labels_by_bundles[0]

    labels_by_names_and_bundles = [name_label+'_'+bundle_label for name_label, bundle_label in zip(labels_by_names, labels_by_bundles)]

    if label_by == 'names':
        labels = labels_by_names
    elif label_by == 'bundles':
        labels = labels_by_bundles
    elif label_by == 'both':
        labels = labels_by_names_and_bundles
    else:
        raise Exception('Specify names, bundles, or both for label_by')

    if label_with_bcs_synapse_count:
        #TODO update the below values, which are from <Nov 2019
        bcs_targets = {
            9004: 42,
            2713: 38,
            8991: 38,
            463: 33,
            467: 20,
            10222: 14,
            9012: 8,
            8995: 5,
            9629: 4,
            9008: 4,
            9686: 3}
        new_labels = []
        for label in labels:
            is_bcs_target = False
            for target in bcs_targets:
                if 'neuron_{}'.format(target+1) in label:
                    is_bcs_target = True
                    label += '_{}'.format(bcs_targets[target])
                    break
            if not is_bcs_target:
                label += '_0'
            new_labels.append(label)
        labels = new_labels

    return labels


def cluster_all(side=side, label_by=label_by): #, optimal_ordering=True):
    filename = config[side][cluster_by]['score filename']
    #raw_scores = np.genfromtxt(filename, delimiter=',')
    #print(neuron_names)
    #distances = 1 - raw_scores[1:, 1:]

    scores = nsf.load_scores(filename)
    distances = 1 - scores

    (headers_are, name_to_skid, skid_to_name,
        skid_to_annots) = nsf.pull_neuron_info(filename)
    bundle_labels = pd.Series({skid: bundles.get_bundle_from_annots(annots)
                               for skid, annots in skid_to_annots.items()})
    bundle_labels = bundle_labels[distances.index]  # Re-order to match distances order
    nerve_labels = pd.Series({skid: bundle[0]
                              for skid, bundle in bundle_labels.items()})
    nerve_labels = nerve_labels[distances.index]  # Re-order to match distances order

    distances = distances.to_numpy()

    pairwise_distances = []
    for row_num in range(len(distances)-1):
        pairwise_distances.extend(distances[row_num:row_num+1, row_num+1:].tolist()[0])

    clustering_iterations = scipy.cluster.hierarchy.linkage(
        pairwise_distances,
        method=config[side][cluster_by]['linkage_method'],
        optimal_ordering=config[side][cluster_by]['optimal_ordering']['all']
    )

    if label_by == 'bundles':
        labels = bundle_labels.to_numpy()
    elif label_by == 'names':
        labels = [name.split(' -')[0] for name in skid_to_name.values()]
    elif label_by == 'both':
        these_bundles = bundle_labels.to_numpy()
        these_names = [name.split(' -')[0] for name in skid_to_name.values()]
        labels = these_names + ': ' + these_bundles

    plt.figure(figsize=(25, 10))
    plt.title('{} side MNs, {}, {} linkage'.format(side, cluster_by, config[side][cluster_by]['linkage_method']))
    scipy.cluster.hierarchy.dendrogram(clustering_iterations, labels=labels)
    plt.show()

    return clustering_iterations

def cluster_by_nerve(side=side, label_by=label_by): #, optimal_ordering=True):
    filename = config[side][cluster_by]['score filename']
    scores = nsf.load_scores(filename)
    distances = 1 - scores

    (headers_are, name_to_skid, skid_to_name,
        skid_to_annots) = nsf.pull_neuron_info(filename)
    bundle_labels = pd.Series({skid: bundles.get_bundle_from_annots(annots)
                               for skid, annots in skid_to_annots.items()})
    bundle_labels = bundle_labels[distances.index]  # Re-order to match distances order
    nerve_labels = pd.Series({skid: bundle[0]
                              for skid, bundle in bundle_labels.items()})
    nerve_labels = nerve_labels[distances.index]  # Re-order to match distances order

    heirarchical_clustering = {}
    for nerve in ['L', 'A', 'V', 'D']:
        in_desired_nerve = nerve_labels.index[nerve_labels == nerve]
        distances_for_desired_nerve = distances.loc[in_desired_nerve, in_desired_nerve].to_numpy()
        #plt.figure()
        #plt.imshow(1-distances_for_desired_nerve)
        #plt.show()
        pairwise_distances = []
        for row_num in range(len(distances_for_desired_nerve)-1):
            pairwise_distances.extend(distances_for_desired_nerve[row_num:row_num+1, row_num+1:].tolist()[0])

        clustering_iterations = scipy.cluster.hierarchy.linkage(
            pairwise_distances,
            method=config[side][cluster_by]['linkage_method'],
            optimal_ordering=config[side][cluster_by].get('optimal_ordering', {}).get('nerve', True)
        )

        plt.title('{} side MNs, {} nerve, {}, {} linkage'.format(side, nerve, cluster_by, config[side][cluster_by]['linkage_method']))
        if label_by == 'bundles':
            labels = bundle_labels.loc[in_desired_nerve].to_numpy()
        elif label_by == 'names':
            these_names = {skid: name.split(' -')[0] for skid, name in skid_to_name.items()}
            labels = pd.Series(these_names).loc[in_desired_nerve].to_numpy()
        elif label_by == 'both':
            these_bundles = bundle_labels.loc[in_desired_nerve]
            these_names = {skid: name.split(' -')[0] for skid, name in skid_to_name.items()}
            these_names = pd.Series(these_names).loc[in_desired_nerve]
            assert all(these_bundles.index == these_names.index), ("Indices don't match:", these_bundles, these_names)
            labels = these_names.to_numpy() + ': ' + these_bundles.to_numpy()
        plt.figure()
        x = scipy.cluster.hierarchy.dendrogram(
            clustering_iterations,
            color_threshold=config[side][cluster_by]['color_threshs'][nerve],
            labels=labels,
            orientation='left'
        )
        plt.gcf().set_size_inches(3, 5)
        plt.tight_layout()
        #fn = '{}_{}nerve_{}_{}{}'.format(side, nerve, cluster_by,
        #                                 config[side][cluster_by]['linkage_method'],
        #                                 '_optimal' if optimal_ordering else '')
        fn = '{}_{}nerve_{}'.format(side, nerve, cluster_by)
        print('Writing file to {}'.format(fn))
        plt.savefig(fn + '.png')
        plt.savefig(fn + '.svg')
        with open(fn + '_labels.txt', 'w') as f:
            for label in x['ivl'][::-1]:
                f.write(label+'\n')
        #plt.show()

        heirarchical_clustering[nerve] = clustering_iterations

    return heirarchical_clustering


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
        print('\nExample usage: python cluster_using_scipy.py cluster_by_nerve side=right label_by=both')
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
