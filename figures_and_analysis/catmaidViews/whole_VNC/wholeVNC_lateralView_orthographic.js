Used for:
DUM neuron lateral view (Fig S2?)

view = JSON.parse('{"target":{"x":160794.03687769693,"y":584117.7413556856,"z":106211.03147928174},"position":{"x":-644182.7062856734,"y":620441.6095625606,"z":87733.06972060402},"up":{"x":-0.045847945561726645,"y":-0.9983423915870635,"z":0.034791307074993796},"zoom":4.75,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();

or is this better?
view = JSON.parse('{"target":{"x":179036.44621878705,"y":480232.48554229306,"z":86153.24812729412},"position":{"x":981316.8995703061,"y":456968.4391206522,"z":159999.53320915994},"up":{"x":-0.031745085431671115,"y":-0.9990410480960226,"z":0.03015350344712347},"zoom":3.7300000000000004,"orthographic":true}'); CATMAID.WebGLApplication.prototype.instances[1].space.view.setView(view.target, view.position, view.up, view.zoom, view.orthographic); CATMAID.WebGLApplication.prototype.instances[1].options.camera_view = view.orthographic ? 'orthographic ' : 'perspective'; CATMAID.WebGLApplication.prototype.instances[1].space.render();
