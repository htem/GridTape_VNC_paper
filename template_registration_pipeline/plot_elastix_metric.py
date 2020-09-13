#!/usr/bin/env python3

import sys

def show_help():
    print('Usage: plot_elastix_metric.py [column_to_plot] [path to elastix output folder]/IterationInfo.0.R*')
    print('    column_to_plot - Typically metric information is in column 1 (for single metric')
    print('    registrations) or columns 1 through 3 (for multimetric registrations). Pick one to plot.')
    print('Example: plot_elastix_metrix.py 3 elastix_Bspline/4spacing_20bendingweight/IterationInfo.0.R*')

if len(sys.argv) <= 2:
    show_help()
    raise SystemExit

import os
import numpy as np
import matplotlib.pyplot as plt

use_exact_metric=False
if not os.path.isfile(sys.argv[1]):
    column_to_analyze = int(sys.argv[1])
    sys.argv.remove(sys.argv[1])
elif use_exact_metric:
    column_to_analyze = 5
else:
    column_to_analyze = 1
#print(sys.argv)

max_iterations = 0
for filename in sys.argv[1:]:
    iteration_log = np.genfromtxt(filename, delimiter='\t', skip_header=1)
    if iteration_log[-1,0] > max_iterations:
        max_iterations = iteration_log[-1,0]

    #TODO validate the header indicates that the selected column contains the thing we think it will contain
    rows_with_metric_recorded = ~np.isnan(iteration_log[:, column_to_analyze])
    iterations_with_metric_recorded = iteration_log[rows_with_metric_recorded, 0]
    metric_values = iteration_log[rows_with_metric_recorded, column_to_analyze]

    plt.plot(iterations_with_metric_recorded, metric_values, '-', alpha=0.5, label=filename.split('elastix_Bspline/')[-1]) #label=np.std(metric_values))
plt.xlabel('Iteration number')
plt.ylabel('Metric value') #TODO pull the name of the metric from the header
#plt.ylim([0, .0005])
plt.xticks(range(0,int(max_iterations)+2,1000))
plt.legend()
plt.show()
