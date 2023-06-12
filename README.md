# GridTape-VNC paper
This code repository accompanies the publication "Reconstruction of motor control circuits in adult Drosophila using automated transmission electron microscopy" by [Jasper Phelps](https://github.com/jasper-tms), [David Hildebrand](https://github.com/davidhildebrand), [Brett Graham](https://github.com/braingram) et al.

We refer to the EM dataset as the Female Adult Nerve Cord, or FANC (pronounced "fancy"). In the years since this paper's publication, a number of labs have continued working on FANC. The latest resources and information about our progress can be found at https://github.com/htem/FANC_auto_recon.

See [GridTapeStage](https://github.com/htem/GridTapeStage) for resources related to building and running GridTape-compatible microscopes (TEMCA-GT).
See the [Lee Lab Resources page](https://www.lee.hms.harvard.edu/resources) for additional resources.
Image data of the EM dataset can be downloaded in python from [BossDB](https://bossdb.org/project/phelps_hildebrand_graham2021).
Image data of the EM dataset can be downloaded as CATMAID-compatible jpg tiles from Google Cloud `gs://vnc1_r066/alignmentV3/jpgs_for_catmaid`. See the [gsutil docs](https://cloud.google.com/storage/docs/gsutil) for instructions.

---

Description of files included in this repository:

### figures_and_analysis
You can recreate the majority of the renderings and plots included in the publication's figures using the files in this folder. See instructions inside.

### neuron_reconstructions
Download skeletons (.swc files) of the neuron reconstructions included in this publication's data release.

### pymaid_utils
A set of python scripts that extend [Philipp Schlegel](https://github.com/schlegelp)'s wonderful [pymaid package](https://github.com/schlegelp/pymaid). Pymaid makes it easy to interact with neuron reconstructions on a [CATMAID](https://catmaid.readthedocs.io/en/stable/) server, and pymaid_utils provides some additional functionality for easily opening a connection to [VirtualFlyBrain's CATMAID server](https://fanc.catmaid.virtualflybrain.org/) where the reconstructions from this publication are hosted, as well as some other utilities. See code for details. Much of the code in `figures_and_analysis` uses this package.

See the repository [htem/pymaid_addons](https://github.com/htem/pymaid_addons) for updated versions of the code in this folder.

### template_registration_pipeline
A set of command line tools that allows users to perform elastic alignment of 3D image stacks, aimed at users wanting to register light microscopy stacks of VNC neurons to the VNC standard atlas. We provide a detailed README and hope that users find this pipeline straightforward to use. The workhorse of this pipeline is [elastix](https://elastix.lumc.nl/).

See the repository [htem/run_elastix](https://github.com/htem/run_elastix) for updated versions of the code in the `run_elastix` subfolder.
