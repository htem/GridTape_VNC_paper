3 image volumes are provided here that represent the synapse density of the EM dataset. Descriptions of each are below. Because GitHub has a file size limit of 100MB per file, the image volumes have been split into a few smaller chunks located inside the folder `image_volumes_chunked`.  You can reassemble the combined images from the chunks by running `python combine_image_volume_chunks.py` from this folder, or combine the stacks manually in ImageJ/Fiji.

---

`FANC_synapsesV3.nrrd` was produced by training a convolutional neural network to predict the location of postsynaptic sites within the FANC EM dataset. Predicted values were stored as an image volume (high probability of being a postsynaptic side -> white, low probability -> black) after which some postprocessing was performed to generate `FANC_synapsesV3.nrrd`:
- Downsampling of the postsynaptic predictions volume from the full EM dataset voxel size of 4.3 x 4.3 x 45nm to 430 x 430 x 450nm.
- 3D Gaussian blurring the downsampled volume with a 2 pixel (~1 micron) sigma.
- Flipping the z axis so that the ventral side of the VNC is at low z slices and the dorsal side is at high z slices, to match the dorsal-ventral orientation of the template.

`FANC_synapsesV3_forAlignment.nrrd` is the image volume that was actually registered to the VNC atlas. It has an offset and different voxel size relative to `FANC_synapsesV3.nrrd`. See bottom section of this text file for more details.

`FANC_synapsesV3_forAlignment.nrrd` was registered to `JRC2018_VNC_FEMALE_4iso.nrrd` (Janelia 2018 Adult Female VNC Template) by running:

> run_elastix FANC_synapsesV3_forAlignment.nrrd -p corresponding_points_FANC.txt -tp corresponding_points_template.txt -s 6 -w 100

(Note that this repository's `template_registration_pipeline/run_elastix/run_elastix` script must be on your PATH to run this.)<br>
(Note that if you try to reproduce this alignment yourself using this command, the results are not guaranteed to be pixel perfect identical
to the transformation provided in the `TransformParameters.*` files in this folder, but your results should be very similar.)<br>
The image volume output by that command is what's contained in `FANC_synapsesV3_forAlignment_aligned.nrrd`

---

In addition to the downsampling and z axis flipping described in the first paragraph above, there are some additional scaling and offset shenanigans that make it complicated to try to use the files in this folder yourself. However, these difficulties are addressed in other scripts in this repository so that you shouldn't have to think about them. See `pymaid_utils/manipulate_and_reupload_catmaid_neurons.py`'s function `get_elastictransformed_neurons_by_skid` for an example of how to account for all of the rescalings, offsets, and flips described in the steps below. If you want to use the files in this folder yourself, you will need to replicate the steps below in your own code:

To get from coordinates in `FANC_synapsesV3.nrrd` (the synapse density of the EM dataset, in the same physical coordinate frame as the EM dataset) to the corresponding location in the VNC template, take the following steps:<br>
1. Shift the coordinate by (-533.2, -533.2, -945)nm. This is (-1.24, -1.24, -2.1) voxels in `FANC_synapsesV3.nrrd`'s voxel scaling of (430, 430, 450)nm, or equivalently is (-124, -124, -21) voxels in the EM dataset's voxel scaling of (4.3, 4.3, 45)nm. (This small offset is due to the CNN not making predictions on the borders of the dataset, so the predictions were shifted up-and-left by this small amount relative to the EM dataset.)
2. Rescale the coordinate to a "fake" scaling that was used in `FANC_syanpsesV3_forAlignment.nrrd`. Instead of the true voxel size of (430, 430, 450)nm, the voxel size was changed to (300, 300, 400)nm. (This global rescaling helped the EM dataset and the VNC template be approximately scaled the same.) So, take your coordinate and multiply x and y each by 300 and divide by 430, and multiply z by 400 and divide by 450.
3. Flip the z axis, using a maximum z coordinate of 435voxels * 400nm/vox = 174000nm. In other words, assign `new_z = 174000 - old_z`. (Why 435 voxels? While `FANC_synapsesV3.nrrd` has 440 slices and so a max z voxel of 439 when 0-indexed, the CNN border clipping clipped 2.1 voxels from the start and end of the stack and resulted in `FANC_synapsesV3_forAlignment.nrrd` only having 436 slices. That was the stack that z-flipping was performed on, so the max z coordinate was 435 when 0-indexed.)
4. Convert from nm to microns by dividing by 1000. At this point, your coordinate is in the coordinate frame represented by the file `FANC_synapsesV3_forAlignment.nrrd` that was used as an input for the elastic alignment of the EM dataset to the VNC template.
5. Perform an elastic transformation of your coordinate (in microns) using the program transformix and the transformation file TransformParameters.FixedVnc1.txt. This maps a micron coordinate value from `FANC_synapsesV3_forAlignment.nrrd` to its corresponding micron coordinate value in the Janelia 2018 Adult Female VNC Template.
6. If you want your coordinate in the VNC template to be in nanometers, multiply by 1000.

To get from coordinates in the VNC template to the corresponding location in the EM dataset, do the above steps but backward:<br>
1. If your coordinate in the VNC template was in nanometers, convert to microns by dividing by 1000.
2. Perform an elastic transformation of your micron coordinate using the program transformix and the transformation file TransformParameters.FixedTemplate.Bspline.txt. This gives you the corresponding location within `FANC_synapsesV3_forAlignment.nrrd`
3. Convert from microns to nm by multiplying by 1000.
4. Flip the z axis by assigning `new_z = 174000 - old_z`.
5. Rescale from the "fake" scaling of `FANC_syanpsesV3_forAlignment.nrrd` to the true scaling of the EM dataset. Multiply x and y each by 430 and divide by 300, and multiply z by 450 and divide by 400.
6. Shift the coordinate by (+533.2, +533.2, +945)nm. You now have the corresponding location in the EM dataset, in nanometers.

