view = JSON.parse('{"target":{"x":131800,"y":250000,"z":71400},"position":{"x":131800,"y":250000,"z":349525.04499601136},"up":{"x":0,"y":-1,"z":0},"zoom":3.35,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
