//In pid 2 (vnc1_V3_LeeLab), 
//Vol 55 is vnc1volume_v2
//Vol 120 is the neuropil volume

//TODO: Update these volume IDs to be the volume IDs on virtualflybrain, where users would be running this code.

//If volumes arent already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.showVolume(55, true, 0xd0d0d0, 0.2, true, false, false)
widget.showVolume(120, true, 0x909090, 0.18, true, false, false)
//Then run this as a separate command once they've loaded
widget.setVolumeSubdivisions(55, 3)
console.log('Done with step 1/2')
widget.setVolumeSubdivisions(120, 3)
console.log('Done with step 2/2')

//If volumes are already loaded, run this
widget = CATMAID.WebGLApplication.prototype.instances[1]
widget.setVolumeStyle(55, true)
widget.setVolumeColor(55, 0xd0d0d0, 0.2)
widget.setVolumeStyle(120, true)
widget.setVolumeColor(120, 0x909090, 0.18)
widget.setVolumeSubdivisions(55, 3)
console.log('Done with step 1/2')
widget.setVolumeSubdivisions(120, 3)
console.log('Done with step 2/2')
