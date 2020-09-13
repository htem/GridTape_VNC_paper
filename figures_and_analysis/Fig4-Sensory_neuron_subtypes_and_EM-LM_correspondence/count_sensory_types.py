#!/usr/bin/env python3

import pymaid
import pymaid_utils as pu

def pull_skids(x):
    return pymaid.get_skids_by_annotation(
        x + ['Paper: Maniates-Selvin, Hildebrand, Graham et al. 2020'],
        intersect=True,
        remote_instance=pu.source_project
    )


def pull_skids_all_nerves(x):
    return (pull_skids(x + ['left T1 leg nerve']) +
            pull_skids(x + ['left T1 accessory nerve']) +
            pull_skids(x + ['left T1 ventral nerve']) +
            pull_skids(x + ['left T1 dorsal nerve']))

club_cho_skids = pull_skids_all_nerves(['T1 leg club chordotonal neuron'])
claw_cho_skids = pull_skids_all_nerves(['T1 leg claw chordotonal neuron'])
hook_cho_skids = pull_skids_all_nerves(['T1 leg hook chordotonal neuron'])
ascending_cho_skids = pull_skids_all_nerves(['T1 leg ascending chordotonal neuron'])
unclassified_cho_skids = pull_skids_all_nerves(['T1 leg chordotonal neuron unclassified subtype'])
chordotonal_skids = (club_cho_skids + claw_cho_skids + hook_cho_skids +
                     ascending_cho_skids + unclassified_cho_skids)

campaniform_skids = pull_skids_all_nerves(['campaniform sensillum'])
hair_plate_skids = pull_skids_all_nerves(['hair plate'])
bristle_skids = pull_skids_all_nerves(['bristle'])
unclassified_skids = pull_skids_all_nerves(['T1 leg sensory neuron unclassified subtype'])
all_skids = (chordotonal_skids + campaniform_skids + hair_plate_skids +
             bristle_skids + unclassified_skids)

txt = (
    f'Total number of left T1 sensory neurons: {len(all_skids)}\n'
    f'   Chordotonal neurons:                  ├──{len(chordotonal_skids)}\n'
    f'      Club chordotonal neurons:          │  ├──{len(club_cho_skids)}\n'
    f'      Claw chordotonal neurons:          │  ├──{len(claw_cho_skids)}\n'
    f'      Hook chordotonal neurons:          │  ├──{len(hook_cho_skids)}\n'
    f'      Ascending chordotonal neurons:     │  ├──{len(ascending_cho_skids)}\n'
    f'      Unclassified chordotonal neurons:  │  └──{len(unclassified_cho_skids)}\n'
    f'   Campaniform sensillum neurons:        ├──{len(campaniform_skids)}\n'
    f'   Hair plate neurons:                   ├──{len(hair_plate_skids)}\n'
    f'   Bristle neurons:                      ├──{len(bristle_skids)}\n'
    f'   Unclassified neurons:                 └──{len(unclassified_skids)}'
)
txt = (
    f'{len(all_skids)}      Total number of reconstructed left T1 leg sensory neurons (out of ~900)\n'
    f'├──{len(chordotonal_skids)}     Chordotonal neurons\n'
    f'│  ├──{len(club_cho_skids)}     Club chordotonal neurons\n'
    f'│  ├──{len(claw_cho_skids)}     Claw chordotonal neurons\n'
    f'│  ├──{len(hook_cho_skids)}     Hook chordotonal neurons\n'
    f'│  ├──{len(ascending_cho_skids)}      Ascending chordotonal neurons\n'
    f'│  └──{len(unclassified_cho_skids)}     Unclassified chordotonal neurons\n'
    f'├──{len(campaniform_skids)}      Campaniform sensillum neurons\n'
    f'├──{len(hair_plate_skids)}      Hair plate neurons\n'
    f'├──{len(bristle_skids)}     Bristle neurons\n'
    f'└──{len(unclassified_skids)}      Unclassified neurons'
)

print(txt)
