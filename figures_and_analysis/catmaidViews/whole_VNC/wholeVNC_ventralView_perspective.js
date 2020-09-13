Used for:
basically nothing, I switched everything to dorsal view I think. Was previously used for:
DUM panel (S?A)
bCS panel (4A & 4B)
PSI panel (S?C)

view = JSON.parse('{"target":{"x":165832.90781649313,"y":567714.2270204102,"z":97720.43039072689},"position":{"x":55331.05695596755,"y":517908.20796411193,"z":788184.560550621},"up":{"x":-0.03011051145717843,"y":-0.9965988619709998,"z":-0.07670766205468525},"zoom":1.48,"orthographic":false}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
