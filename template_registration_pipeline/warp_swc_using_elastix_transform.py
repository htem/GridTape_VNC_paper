#!/usr/bin/env python3

import numpy as np
import os
import subprocess

def show_help():
    print('Usage: warp_swc_using_elastix_transform.py swc_file transform_file [swc_side=left] [generate_flipped_swc=True]')
    print('Takes the swc_file and uses elastix\'s function transformix to apply the transformation specified by transform_file.')
    print('This function is mainly intended for transforming neuron tracings from light or electron microscopy into the VNC atlas coordinate system.')
    print('Set swc_side to be the side of the VNC the neuron was originally on. Then the output files will be correctly named with _left or _right')
    print('to indicate the position of the output neurons within the VNC atlas.')
    print('Set generate_flipped_swc to True to generate both the _left and _right outputs.')

def warp_swc_using_elastix_transform(swc_file, transform_file, swc_side='left', generate_flipped_swc=True):
    assert '.swc' in swc_file
    assert swc_side in ['left', 'right']

    swc_data = np.genfromtxt(swc_file)
    #swc_data[:, 4]=83-swc_data[:, 4] #Reverse z if the tracing and the elastix alignment were done on flipped versions of a stack. This was a one-time thing


    with open(swc_file.replace('.swc', '_transformixInput.swc'), 'w') as f_out:
        f_out.write('point\n{}\n'.format(len(swc_data)))
        for a,b,c,d,e,f,g in swc_data:
            f_out.write("%f %f %f\n"%(c,d,e))
    print('Done making transformix input')


    transformix_call = 'transformix -out ./ -tp {} -def {}'.format(transform_file, swc_file.replace('.swc', '_transformixInput.swc'))
    #print(transformix_call)
    try:
        subprocess.run(transformix_call.split(' '))
    except FileNotFoundError:
        print('transformix executable not found on $PATH. Terminating.')
        return


    #Take transformix's outputpoints.txt and pull out just the OutputPoint column
    with open('outputpoints.txt', 'r') as f_in:
        with open(swc_file.replace('.swc', '_transformixOutput.swc'), 'w') as f_out:
            for l in f_in.readlines(): 
                coords = l.split('OutputPoint = [ ')[1].split(' ]')[0] 
                #print(coords)
                f_out.write(coords+'\n') 


    #Convert those points to the target project space (which in this case is just multiplying by 1000 to convert um to nm)
    swc_data = np.genfromtxt(swc_file)
    transformixed_data = np.genfromtxt(swc_file.replace('.swc', '_transformixOutput.swc'))
    swc_data[:, 2:5] = transformixed_data
    swc_data[:, 2:5] *= 1000


    #Write the final swc in a CATMAID-readable format
    output_dir = os.path.dirname(transform_file) #Store the final output in the same folder as the transform_file
    if swc_side == 'left':
        filename_modifier = '_inTemplateSpace_left.swc'
    else:
        filename_modifier = '_inTemplateSpace_right.swc'
    with open(os.path.join(output_dir,swc_file.replace('.swc', filename_modifier)), 'w') as fout:
        for a,b,c,d,e,f,g in swc_data:
            fout.write("%d %d %f %f %f %d %d\n"%(a,b,c,d,e,f,g))

    #If the output swc was not put into the same folder as the source swc, make a link to the output in the same folder as the source swc
    if os.path.dirname(swc_file) is not output_dir:
        link_name = os.path.join(os.path.dirname(swc_file), swc_file.replace('.swc', filename_modifier))
        if os.path.exists(link_name):
            os.remove(link_name)
        os.symlink(os.path.join(output_dir,swc_file.replace('.swc', filename_modifier)), link_name)

    if generate_flipped_swc:
        swc_data[:, 2] = 263200-swc_data[:, 2] #Left-right flip across the template's midline.
        if swc_side == 'left':
            filename_modifier = '_inTemplateSpace_right.swc'
        else:
            filename_modifier = '_inTemplateSpace_left.swc'
        with open(os.path.join(output_dir,swc_file.replace('.swc', filename_modifier)), 'w') as fout:
            for a,b,c,d,e,f,g in swc_data:
                fout.write("%d %d %f %f %f %d %d\n"%(a,b,c,d,e,f,g))

        #If the output swc was not put into the same folder as the source swc, make a link to the output in the same folder as the source swc
        if os.path.dirname(swc_file) is not output_dir:
            link_name = os.path.join(os.path.dirname(swc_file), swc_file.replace('.swc', filename_modifier))
            if os.path.exists(link_name):
                os.remove(link_name)
            os.symlink(os.path.join(output_dir,swc_file.replace('.swc', filename_modifier)), link_name)


    #Remove the intermediate files
    os.remove(swc_file.replace('.swc', '_transformixInput.swc'))
    os.remove('transformix.log')
    os.remove('outputpoints.txt')
    os.remove(swc_file.replace('.swc', '_transformixOutput.swc'))



def main():
    import sys
    if len(sys.argv) == 1:
        show_help()
        return
    warp_swc_using_elastix_transform(*sys.argv[1:])

if __name__ == '__main__':
    main()

