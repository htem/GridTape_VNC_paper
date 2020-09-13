#Put videos side by side
in1=FANC_space_motor_neurons.mp4
in2=FANC_space_sensory_neurons.mp4
in3=atlas_space_motor_and_sensory_neurons.mp4

ffmpeg -i "$in1" -i "$in2" -i "$in3" -filter_complex "[0]crop=in_w-200:in_h[c0]; [1]crop=in_w-200:in_h[c1]; [2]crop=in_w-300:in_h[c2]; [c0][c1]hstack[h1]; [h1][c2]hstack" tmp.mp4

#Put a text overlay on a video
#https://stackoverflow.com/questions/17623676/text-on-video-ffmpeg/17624103
ffmpeg -i tmp.mp4 -vf drawtext="text='Motor neurons': fontcolor=black: fontsize=72: x=90: y=100",drawtext="text='Sensory neurons': fontcolor=black: fontsize=72: x=740: y=100",drawtext="text='Neurons aligned
   to VNC atlas': fontcolor=black: fontsize=60: x=1460: y=75" VideoS2.mp4

rm tmp.mp4
