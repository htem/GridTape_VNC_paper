## Data analysis and figure generation code
This folder contains 3 main types of files:

### 1. Python code
Requires python3.6+.<br>
Install the package `pymaid` using the instructions [here](https://pymaid.readthedocs.io/en/latest/source/install.html). (Do NOT try to install it via `pip install pymaid`, as that gets you a completely different, unrelated package.)<br>
You may also need to install other packages depending on what you already have in your python environment, but the rest can be installed with `pip`.


### 2. Catmaid rendering configurations
For each figure panel showing an image of reconstructed neurons, you can load those neurons into a CATMAID 3D viewer yourself to explore the neurons in more detail. To do this, navigate to the folder in this directory corresponding to the figure panel you're interested in, and following these instructions:
1. Open CATMAID. For Fig 3A-B, use [this link to the EM-space neurons](https://catmaid3.hms.harvard.edu/catmaidvnc/?pid=2&zp=168300&yp=583144.5&xp=186030.9&tool=tracingtool&sid0=10&s0=7). For all other figures, use [this link to the atlas-space neurons](https://catmaid3.hms.harvard.edu/catmaidvnc/?pid=59&zp=71200&yp=268000&xp=131600&tool=tracingtool&sid0=49&s0=1).
2. Open the 3D viewer widget with the blue "3D" button on the top bar of the page.
3. In the Selection 1 widget that appears beneath the 3D viewer widget, press "Open JSON", and in the Open dialog navigate to the subfolder of this repository corresponding to the figure you're interested. Find the .json file in that figure's folder, which contains a list of neurons and a color for each neuron. Neurons should now appear into your 3D viewer.
4. To set other view settings to exactly match the paper's figures, you'll need to open your browser console ([instructions](https://www.wickedlysmart.com/hfjsconsole/)), then paste a few lines of javascript code into that console. First, open the `set_volume_shading.js` file within the relevant subfolder of this directory, read the instructions there and copy the relevant section, and paste those few lines of code into your browser console. Volume meshes should now appear. Second, open the `set_camera_position.js` file, copy-paste the one line in that file into your broswer, and the camera view should change. Finally, open `export_settings.txt` and manually set a few last settings in the 3D viewer by following the instructions in that file.

### 3. Matlab code
We used MATLAB2018b but didn't use any particularly fancy functions, so the code here will almost certainly work with other versions of MATLAB. No prerequisites, just boot up MATLAB and run any .m files you see in these folders.
