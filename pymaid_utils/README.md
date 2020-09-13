## pymaid_utils
This package contains 3 modules:

#### `connections.py`
Opens a connection to a CATMAID server, reading the needed URL and account info from a config file stored in the `connection_configs` folder. A credentials file is provided for connecting to VirtualFlyBrain's CATMAID instance where the resconstructions from this paper are hosted.

#### `make_3dViewer_json.py`
A collection of functions to create json configuration files for the CATMAID 3D viewer widget, by providing a mapping between colors and lists of annotations to search for. The workhorses here are `make_json_by_annotations` for converting annotation lists to skeleton ID lists, and `write_catmaid_json` for writing out a correctly formatted file.

#### `manipulate_and_reupload_catmaid_neurons.py`
Pull neuron data from one CATMAID project, manipulate the neuron in some way, and reupload it to a target project. These functions require that you add credentials for a target project in the connections_config file for which you have API annotation privileges. This is only relevant for users that have their own CATMAID instances - users looking to just pull neuron data from VirtualFlyBrain for examining can ignore this module. **Be careful with these functions, as they directly modify data on your CATMAID server.**

Uploaded neurons are given a 'linking annotation' that allows uploaded neurons to know which source neuron they were generated from. This linking annotation enables the function `push_all_updates_by_annotations`/`push_all_updates_by_skid` to straightforwardly updated linked neurons in a target project if their source neuron has been modified somehow, for instance by adding annotations or tracing. This ensures that duplicate neurons are not made in the target project when such modifications are pushed, and also ensures that the skeleton ID of the target neuron never changes, which means code or .json files that identify neurons by their skeleton ID don't need to be updated after updating a linked neuron.
1. `copy_neurons`: No modifications to the neuron
2. `translate_neurons`: Apply a translation
3. `affinetransform_neurons`: Apply an affine transformation
4. `elastictransform_neurons`: Apply an elastic transformation. Uses the function [transformix](https://manpages.debian.org/testing/elastix/transformix.1.en.html) from the [elastix](https://elastix.lumc.nl/) package, which must be installed. Used in this paper to take [neurons reconstructed in the VNC EM dataset](https://catmaid3.hms.harvard.edu/catmaidvnc/?pid=2&zp=168300&yp=583144.5&xp=186030.9&tool=tracingtool&sid0=10&s0=7) and warp them them to the coordinate space of the VNC standard atlas (JRC2018_FEMALE_VNC), and upload those warped neurons to a [separate catmaid project](https://catmaid3.hms.harvard.edu/catmaidvnc/?pid=59&zp=71200&yp=268000&xp=131600&tool=tracingtool&sid0=49&s0=1). All neuron renderings after Figure 3 were made in this atlas-space CATMAID project.
5. `volume_prune_neurons`: Prune a neuron to the parts that are within a CATMAID volume object. Used in this paper to prune neurons down to the regions within the VNC's neuropil.
6. `radius_prune_neurons`: Prune a neuron to only the nodes that have a certain radius. Used in this paper to prune motor neurons down to their primary neurites.

#### Additionally, `__init__.py`
Upon importing this package, `__init__.py` opens a connection to CATMAID using `connetions.connect_to_catmaid()`, which uses the default parameters at `connection_configs/catmaid_configs.json`. Then, `__init__.py` shares access to that connection object with each of the 3 modules above, so that changes in the connection (like changing project ID) will be seen by each of the modules.

To use `pymaid_utils` to easily open a CATMAID connection for use by `pymaid` functions, you can do something like the following:

    import pymaid  # https://pymaid.readthedocs.io/en/latest/index.html
    import pymaid_utils as pu
    pu.source_project.make_global()
    pu.set_source_project_id(7)  # You can set the project ID within your scripts via this function instead of changing it in the config files
    
    pymaid.whatever_pymaid_function_you_want_to_use(args)
    
OR

    import pymaid
    import pymaid_utils as pu
    pu.set_source_project_id(7)
    
    pymaid.whatever_pymaid_function_you_want_to_use(args, remote_instance=pu.source_project)  # If you don't make_global() the pymaid_utils project, you need to explicitly pass the project to pymaid functions
