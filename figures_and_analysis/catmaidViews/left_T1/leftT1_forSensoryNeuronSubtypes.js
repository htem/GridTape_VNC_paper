view = JSON.parse('{"target":{"x":83082.30426451309,"y":451139.38474543224,"z":106727.46603280523},"position":{"x":183392.98378582072,"y":321725.212082608,"z":-598982.4286827481},"up":{"x":-0.026808039859252637,"y":-0.983913775545829,"z":0.17662109525776518},"zoom":20.5,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].updateCameraView(view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].space.render();