Considering using for:
Left T1 sensory neuron renderings (Fig 3bcd)
view = JSON.parse('{"target":{"x":86725.08628093463,"y":439416.52030479367,"z":129316.66927038648},"position":{"x":56893.03619365847,"y":508139.9426171637,"z":844097.5771976897},"up":{"x":-0.008302155568219772,"y":-0.995609400602373,"z":0.09323623568693042},"zoom":6.73,"orthographic":false}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
