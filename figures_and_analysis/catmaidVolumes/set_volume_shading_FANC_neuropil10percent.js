//In pid 2 (vnc1_V3_LeeLab), 
//Vol 55 is vnc1volume_v2
//Vol 120 is the neuropil volume

//TODO: Update these volume IDs to be the volume IDs on virtualflybrain, where users would be running this code.

//If volumes arent already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.showVolume(120, true, 'black', 0.10, true, false, false)

//If volumes are already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.setVolumeStyle(120, true)
widget.setVolumeColor(120, 0x000000, 0.10)
