Used for:
Fig 1 whole dataset rendering

view = JSON.parse('{"target":{"x":173400.2193066409,"y":484302.03498628986,"z":148668.36130233138},"position":{"x":161864.89405117382,"y":420784.8642897073,"z":-572905.766081277},"up":{"x":-0.002415518336768988,"y":-0.9961418162265792,"z":0.08772483819294506},"zoom":3.7300000000000004,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();

Rotation videos of all traced neurons
view = JSON.parse('{"target":{"x":167340.17152164548,"y":479140.8575660078,"z":89894.78118453478},"position":{"x":216458.3685709426,"y":415615.92559326574,"z":-630097.3727643463},"up":{"x":-0.002415518336769021,"y":-0.9961418162265798,"z":0.08772483819294513},"zoom":3.7300000000000004,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
