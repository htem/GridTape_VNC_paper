Used for:
T1MNprimaryNeuriteBundles panel

view = JSON.parse('{"target":{"x":162121.00698186294,"y":438150.7256985503,"z":113026.71297807989},"position":{"x":237473.92634043476,"y":313662.81868868,"z":-478267.2319288604},"up":{"x":-0.03535614124458909,"y":-0.978835140049879,"z":0.20157309314447094},"zoom":4.23,"orthographic":false}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
