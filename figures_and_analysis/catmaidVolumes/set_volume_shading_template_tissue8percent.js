
//TODO: Update these volume IDs to be the volume IDs on virtualflybrain, where users would be running this code.

//If volumes arent already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.showVolume(127, true, 'black', 0.08, true, false, false)

//If volumes are already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.setVolumeStyle(127, true)
widget.setVolumeColor(127, 0x000000, 0.08)
