import seaborn as sns
from pandas_ods_reader import read_ods  # pip install pandas-ods-reader
import matplotlib.pyplot as plt

path = 'area_measurements.ods'

# Sheet 1
sheet_idx = 1
df1 = read_ods(path, sheet_idx)

df_left_T1_motor = df1.loc[df1['type'] == 'motor']
df_left_T1_motor = df_left_T1_motor.drop([55])
df_left_T1_bCS = df1.loc[df1['type']=='bCS']
df_left_T1_bCS = df_left_T1_bCS.drop([54])

df_left_T1 = df_left_T1_motor.append(df_left_T1_bCS, ignore_index=True)
df_left_T1['nerve'] = 'left_T1'

# Sheet 2
sheet_idx = 2
df2 = read_ods(path, sheet_idx)

df_right_T2_motor = df2.loc[df2['type'] == 'motor']
df_right_T2_bCS = df2.loc[df2['type']=='bCS']

df_right_T2 = df_right_T2_motor.append(df_right_T2_bCS, ignore_index=True)
df_right_T2['nerve'] = 'right_T2'

# Sheet 3
sheet_idx = 3
df3 = read_ods(path, sheet_idx)

df_right_T3_motor = df3.loc[df3['type'] == 'motor']
df_right_T3_bCS = df3.loc[df3['type']=='bCS']

df_right_T3 = df_right_T3_motor.append(df_right_T3_bCS, ignore_index=True)
df_right_T3['nerve'] = 'right_T3'

# Combine
df = df_left_T1.append(df_right_T2, ignore_index=True)
df = df.append(df_right_T3, ignore_index=True)


# Plot
df.rename(columns={'average': r'Axon area ($\mu$m$^2$)'}, inplace=True)
df.loc[df.type == 'motor', 'type'] = 'Motor\nneurons'
df.loc[df.type == 'bCS', 'type'] = 'bCS\nneurons'
colors = ['#00cccc','#ff0080']

g = sns.catplot(x='type', y=r'Axon area ($\mu$m$^2$)', col='nerve', data=df, palette=colors)
plt.gcf().set_size_inches(5, 3.5)
plt.tight_layout()
plt.savefig('bCS_vs_MN_axon_area.png')
plt.savefig('bCS_vs_MN_axon_area.svg')
plt.show()
