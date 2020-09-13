#!/usr/bin/env python3

import numpy as np

import nrrd  # pip install pynrrd

chunk_map = (
    ('FANC_synapsesV3.nrrd',
        ('image_volumes_chunked/FANC_synapsesV3_chunk1.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_chunk2.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_chunk3.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_chunk4.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_chunk5.nrrd')),
    ('FANC_synapsesV3_forAlignment.nrrd',
        ('image_volumes_chunked/FANC_synapsesV3_forAlignment_chunk1.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_chunk2.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_chunk3.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_chunk4.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_chunk5.nrrd')),
    ('FANC_synapsesV3_forAlignment_aligned.nrrd',
        ('image_volumes_chunked/FANC_synapsesV3_forAlignment_aligned_chunk1.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_aligned_chunk2.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_aligned_chunk3.nrrd',
         'image_volumes_chunked/FANC_synapsesV3_forAlignment_aligned_chunk4.nrrd'))
)


def combine_chunks(chunk_map=chunk_map):
    """
    Concatenate different nrrd image files along their z axis
    into a single image file.
    """
    for line in chunk_map:
        output_fn = line[0]
        chunk_fns = line[1]
        chunks = []
        for chunk_fn in chunk_fns:
            print('Loading {}'.format(chunk_fn))
            chunk_data, metadata = nrrd.read(chunk_fn)
            chunks.append(chunk_data)
        assert all([chunk.shape[:2] == chunks[0].shape[:2] for chunk in chunks[1:]])
        
        print('Concatenating chunks...')
        output_array = np.concatenate(chunks, axis=2)

        print('Saving concatenated volume to {}. This will take ~30 seconds.'.format(output_fn))
        nrrd.write(output_fn, output_array, header=metadata)


def split_into_chunks(input_fn, chunk_axis=2, chunk_size=100,
                      output_folder='image_volumes_chunked'):
    """
    Splits a .nrrd stack into chunks of 100 z slices.
    Change chunk_axis to 0 for splitting along x axis, 1 for splitting along y
    """
    print('Loading {}'.format(input_fn))
    input_array, metadata = nrrd.read(input_fn)
    n_chunks = (input_array.shape[chunk_axis] - 1) // chunk_size + 1
    for i in range(n_chunks):
        slice_start = i * chunk_size
        slice_end = min((i + 1) * chunk_size, input_array.shape[chunk_axis])
        chunk_array = input_array[:, :, slice_start:slice_end]
        output_fn = output_folder + '/' + input_fn.replace('.nrrd', '_chunk{}.nrrd'.format(i+1))
        print('Writing chunk {} of {} to {}'.format(i+1, n_chunks, output_fn))
        nrrd.write(output_fn,
                   chunk_array,
                   header=metadata)


if __name__ == "__main__":
    combine_chunks()
