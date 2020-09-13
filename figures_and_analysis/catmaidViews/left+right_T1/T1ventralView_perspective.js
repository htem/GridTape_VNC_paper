Used for:
multinerve neuron ventral view

view = JSON.parse('{"target":{"x":165168.03546791853,"y":442293.2362382599,"z":67241.8684460464},"position":{"x":63898.916782964894,"y":581185.520884623,"z":765080.0339189746},"up":{"x":-0.0167373413212247,"y":-0.9815002191321998,"z":0.19072802953139917},"zoom":3.98,"orthographic":false}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
