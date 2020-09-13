#!/usr/bin/env/python3

import os

import pymaid_utils as pu
import nblast_score_files as nsf

colormap = (
    (['campaniform sensillum', 'tracing from electron microscopy'], 'matlab4'),
    (['chordotonal neuron', 'tracing from electron microscopy'], 'matlab2'),
    (['hair plate', 'tracing from electron microscopy'], 'matlab3'),
    (['tracing from light microscopy'], 'black')
)


def annots_to_color(annots, colormap=colormap, as_hex=True):
    matches = []
    for row in colormap:
        search_terms = row[0]
        if all([i in annots for i in search_terms]):
            matches.append(row[1])
    if len(matches) > 1:
        print(annots)
        print(matches)
        raise Exception('Multiple matches!')
    elif len(matches) == 0:
        print(annots)
        raise Exception('No matches found!')

    if as_hex:
        return pu.colorword_to_hex[matches[0]]
    else:
        return matches[0]


scores_fn = '../../nblast_scores/catmaid_nblast_scores_id93_LMxEM_leftT1_sensoryNeurons.csv'
output_folder = 'jsons'
os.makedirs(output_folder, exist_ok=True)
scores = nsf.load_scores(scores_fn)
(headers_are, name_to_skid, skid_to_name,
    skid_to_annots) = nsf.pull_neuron_info(scores)

for lm_neuron in scores.index:
    if 'bCS' in skid_to_annots[lm_neuron]:
        top_n_hits = 2
    else:
        top_n_hits = 5
    top_hits = nsf.get_top_hits(scores, lm_neuron, top_n_hits).index
    skids_to_colors = {lm_neuron: annots_to_color(skid_to_annots[lm_neuron])}
    for hit_skid in top_hits:
        hit_annots = skid_to_annots[hit_skid]
        skids_to_colors[hit_skid] = annots_to_color(hit_annots)

    pu.write_catmaid_json(
        skids_to_colors,
        os.path.join(output_folder, skid_to_name[lm_neuron]+' and top '+str(top_n_hits)+ ' hits')
    )
