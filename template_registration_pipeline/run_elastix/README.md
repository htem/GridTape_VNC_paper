## A pipeline for running elastix to register two 3D image stacks.
Intended use is registering neuroimaging data from one individual to a standard template of the imaged brain structure. Recommended parameters in this pipeline have been tuned for aligning adult Drosophila ventral nerve cords, which are ~450 x 200 x 150 microns in size. If you're trying to use this to register structures of different spatial sizes, you may need to tune parameters yourself.

THIS CODE IS INCLUDED IN THIS REPOSITORY FOR POSTERITY, BUT CONTINUED DEVELOPMENT OF HAS BEEN MOVED TO [A SEPARATE REPOSITORY](https://github.com/htem/run_elastix). Check that repository for the latest code.

---

## Usage Manual

### Step 0: Prerequisites
**A.** [Download elastix](https://elastix.lumc.nl/download.php) and add its bin/ folder to your PATH so that `elastix` and `transformix` can be called from the command line.

**B.** Make sure this folder is on your PATH so that `run_elastix` and `invert_elastix` can be called from the command line.

**C.** Download the standard template you want to align to. The most recent Drosophila brain and VNC standard templates are available from [Janelia](https://www.janelia.org/open-science/jrc-2018-brain-templates)

**D.** Open `run_elastix` and change the line starting with `template=` to point to your template file. By default, `run_elastix` tries to look for a file named `JRC2018_VNC_FEMALE_4iso.nrrd` (the standard template of the female VNC) in the same folder as the script is in (so, this folder).

**E.** If your computer has less than 32 cores, open `run_elastix` and change the line `n_threads=30` be some number equal to or slightly less than the number of cores on your computer.


### Step 1: Prepare input files
For registering light microscopy data of neurons, you need to have a neuropil channel and a neuron channel.
- **1.0** Open your image stack in [Fiji](https://fiji.sc/) or your favorite image stack processing software.

- **1.1** Rotate the image stack so that anterior is near the top of the image (low y values) and posterior is down (high y values). (This step isn't strictly necessary but it makes it more likely that affine alignment will be correct on the first try.)

- **1.2** If necessary, flip the z axis so that your stack is in the same orientation as the standard template, which is to have the ventral side of the VNC at the low z slices and the dorsal side of the VNC at the high z slices.

- **1.3** Make sure your stack's scale is set correctly (`Analyze > Set Scale`) to whatever resolution your microscope was set to aquire at. The female VNC's neuropil measures approximately 425 microns anterior-to-posterior, 175 microns left-to-right, and 120 microns dorsal-to-ventral. Verify that your VNC is approximately that size. (Fiji tip: If you need to set the z voxel size to be different than the x/y voxel size, first in the Set Scale menu press "Click to Remove Scale" and press "OK", then re-open the Set Scale menu and enter the z voxel size and press "OK", then re-open the Set Scale menu a third time and enter the x/y voxel size and press "OK". In my version of Fiji, Set Scale operations don't apply to the z axis if it's already set, which is why it's necessary to first Remove Scale.)

- **1.4** Split the neuropil channel and neuron channel into separate stacks, and `Save As > Nrrd` to generate separate nrrd files for the neuropil and the neuron.

- **1.5** If your goal is to trace the neuron and then warp it into the template's coordinate space, you can now trace your neuron in this rotated and potentially z-flipped image stack. The [Simple Neurite Tracer](https://imagej.net/SNT) plugin in Fiji is one good way to do this. In Step 4b you'll warp your tracing of the neuron in the unaligned image stack to be in the aligned image's space. In my experience, it's better to trace the unaligned neuron so that if you make multiple attempts at the registration, you can warp the unaligned neuron using each of those registration parameters to see how the aligned neuron looks without needing to trace multiple different versions of the aligned neuron.


### Step 2: Affine alignment
- **2.1** Run the following in a bash terminal, replacing the filename with your neuropil stack's filename:<br>
`run_elastix 99Z99-Gal4_vnc7_60x_2019_09_19_neuropil.nrrd -a`<br>
This example runs affine (-a) alignment, with your image as the moving image and the standard template as the fixed image. You can reverse the fixed and moving images by passing a `-r` argument. This should take just ~2 minutes.

- **2.2** Inspect the output image (result.0.nrrd) in Fiji to make sure your neuropil channel has been appropriately scaled, translated, and rotated to be overlayed as well as possible onto the template image. To visually inspect alignment quality, I find it easiest to open result.0.nrrd and the template in Fiji and merge the two as separate color channels (`Image > Color > Merge Channels`), but then view them in Grayscale mode (`Image > Color > Channels Tool > Grayscale`) and toggle between the two channels.

- **2.3** If the results are good, move on to Step 3.1. If the results are bad, see the troubleshooting advice in Step 3.3.


### Step 3: Elastic (Bspline) alignment
- **3.1** Run the following in a bash terminal, replacing the filename with your neuropil stack's filename:<br>
`run_elastix 99Z99-Gal4_vnc7_60x_2019_09_19_neuropil.nrrd -b`<br>
This example runs elastix Bspline (-b) alignment, again using your image as the moving image and the standard template as the fixed image. This uses the default elasticity parameters of `grid spacing = 12` and `bending weight = 100`.

By far the most important parameters to tune to get good alignment are the grid spacing (-s) and bending weight (-w). -s is a value specified in microns that determines how small of cubes the image volume is split up into, with each cube being warped with different parameters. Therefore, -s determines how small of features can be warped independently from their neighbors. Smaller -s means smaller cubes, meaning usually better registration results, but at the cost of longer runtime. -w influences how strongly the parameters are encouraged to have small values, which helps reduce unrealisticly large distortions. Your goal is to find a proper value of -w that allows for just enough elasticity to get a good alignment, without allowing unrealistic distortions. For mathematical reasons, optimal values of -w scale with the value of -s (i.e. larger -s values require larger -w).<br>
Some good -s/-w pairings to try first, depending on how much time you're willing to wait:<br>
`-s 24 -w "400 800"`      :  Runs 2 alignments in about 6 minutes each (on 30 cores)<br>
`-s 12 -w "40 200"`       :  Runs 2 alignments in about 10 minutes each (on 30 cores)<br>
`-s 8 -w "20 80"`         :  Runs 2 alignments in about 17 minutes each (on 30 cores)<br>
`-s 6 -w "15 60"`         :  Runs 2 alignments in about 25 minutes each (on 30 cores)<br>
`-s 4 -w "10 40"`         :  Runs 2 alignments in about 45 minutes each (on 30 cores)<br>
Note how multiple values for -w can be specified by putting them in quotes separated by spaces. In this way you can use a single `run_elastix` command to perform multiple sequential alignments with different elasticities. This can also be done with -s, e.g.:<br>
`run_elastix sample1_neuropil.nrrd -b -s "4 6" -w "10 20 80"`<br>
This would run runs 6 Bspline (-b) alignments with each combination of the given -s and -w  values (i.e. 4&10, 4&20, 4&80, 6&10, 6&20, and 6&80). It's often useful to run a few different alignments in this way, go do other stuff, and then come back when it's finished.

- **3.2** Inspect results in Fiji. There is no straightforward way to mathematically quantify how good an alignment is. Metrics like correlation coefficients don't reliably differentiate good from mediocre alignments. Inspecting by eye is the way to go unless you know of a better approach. Aim to have the regions of the dataset that you care most about to be aligned within some tolerance for error, which depends on your application. 1 micron (2-3 pixels of error) is often a good bar to aim for. If you're satisfied with the results, you're done! Jump to step 4. If not, continue to 3.3.

- **3.3** If you aren't satisfied with the results you got with any combinations of -s and -w, the most surefire way to improve the registration is to manually add correspondence points: find corresponding locations in the two image volumes and put those point locations into two text files, one listing the locations in your image, the other listing the corresponding locations in the template. See `corresponding_points_image.txt` and `corresponding_points_template.txt` in this folder for examples of how to format these points files. You can either specify the points in voxel coordinates, in which case put "index" as the first line of the text file, or in physical coordinates (that is, in microns), in which case put "point" as the first line of the text file.

- **3.4** Return to step 3.1 to rerun alignment, but add `-p your_points_in_image.txt -tp your_points_in_template.txt` as arguments to your `run_elastix` command. Then, elastix will pull your corresponding points toward each other. Note that you can also add corresponding points to affine alignment commands (Step 2.1) via the same -p and -tp arguments.

- **3.optional** If you want to try to get your registrations to go better without having to manually add correspondence points, you'll need to learn more about how elastix works by reading the [elastix documentation](https://elastix.lumc.nl/doxygen/index.html). Then you can tinker with the parameter file `elastixParams_Bspline.txt` yourself.

#### Step 4a: Apply the transformation to your neuron image stack
- **4a.1** `transformix -in your_neuron_stack.nrrd -out ./ -tp path/to/your/TransformParameters.0.txt`

#### Step 4b: Apply the transformation to your traced neuron
- **4b.1** Warping a neuron tracing (a set of points) requires the inverse of the function that was required to warp an image stack. To generate the inverse of the parameters you generated above, run `invert_elastix your_stack_name_elastix_to_fixed_template/elastix_Bspline/4spacing_20weight`, replacing the path with the path to the folder containing your best alignment. This takes about 10 minutes on 30 cores.
- **4b.2** Inspect the output images (`result.0.composedForwardAndInverseTransforms.nrrd` and `result.1.nrrd`) to make sure the inversion went well. The only time I've seen inversions not go well is if your image data is close to the right edge (high x) or the bottom edge (high y) of the stack, sometimes there can be weird artifacts at those edges. If you see this, expand your stack in x and/or y and try realigning and then re-inverting.
- **4b.3** Warp your neuron tracing using the inverted parameters by running `warp_swc_using_transformix.py your_unaligned_neuron_tracing.swc blah/elastix_Bspline/4spacing_20weight/inverted_6spacing/TransformParameters.1.txt`. Be sure to use `TransformParameters.1.txt`, but change the other parts of this command to point to your files.
