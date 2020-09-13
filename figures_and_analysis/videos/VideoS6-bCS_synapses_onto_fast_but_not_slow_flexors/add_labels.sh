#Note that the newlines in the middle of the text= commands are actually newlines that get put into the labels.
ffmpeg -i catmaid_3d_view.webm -vf \
drawtext="text='EM neuron most similar to
fast flexor motor neuron': fontcolor=white: fontsize=36: x=40: y=40: box=1: boxcolor=#0000ff: boxborderw=10",\
drawtext="text='EM neuron most similar to
slow flexor motor neuron': fontcolor=gray: fontsize=36: x=40: y=120: box=1: boxcolor=#ffff00: boxborderw=10:",\
drawtext="text='left T1 bCS neurons': fontcolor=white: fontsize=36: x=662: y=68: box=1: boxcolor=#a2142f: boxborderw=10",\
drawtext="text='right T1 bCS neurons': fontcolor=white: fontsize=36: x=650: y=120: box=1: boxcolor=#ff0000: boxborderw=10",\
drawtext="text='synapses from bCS onto
fast flexor motor neuron': fontcolor=black: fontsize=36: x=1139: y=75" \
tmp.mp4

ffmpeg -i tmp.mp4 -i synapse.png -filter_complex "[0][1] overlay=1075:79" Video_S6.mp4 -y

rm tmp.mp4
