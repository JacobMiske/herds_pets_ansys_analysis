import os
import re
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from matplotlib import rcParams

# Set plot parameters
rcParams['font.family'] = 'serif'
rcParams['font.size'] = 16

# Directory containing the CSV files
directory = "data/paper_results/deployment_test"

# Initialize lists to collect the data
pet_data_EI = []
short_data_EI = []
long_data_EI = []

pet_data_F = []
short_data_F = []
long_data_F = []

def process_file(filepath):
    """
    Process each CSV file to extract relevant data.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        tuple: A tuple containing the category (str), EI data (tuple), and force data (tuple).
    """
    df = pd.read_csv(filepath)
    alpha = re.search(r'alpha_([0-9.]+)_', os.path.basename(filepath)).group(1)
    scale = 1000.0**2
    ind = len(df['FX']) - 1

    length = df['L'][ind]
    displacement = df['Displacement'][ind]
    fx, fy, fz = df['FX'][ind], df['FY'][ind], df['FZ'][ind]
    f = max(abs(fx), abs(fy), abs(fz))
    EI = length**3 * f / (3.0 * displacement)

    data_point_EI = (length / 1000.0, EI / scale)
    data_point_F = (length / 1000.0, f)

    if "l1" in filepath:
        return ('pet', data_point_EI, data_point_F)
    elif "cells_6" in filepath and 1.07 <= float(alpha) <= 2.97:
        return ('short', data_point_EI, data_point_F)
    elif float(alpha) <= 2.96:
        return ('long', data_point_EI, data_point_F)

# List all files that need to be processed
filepaths = glob.glob(os.path.join(directory, '*_cant_x.csv'))

# Use ThreadPoolExecutor to process files in parallel
with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = [executor.submit(process_file, filepath) for filepath in filepaths]
    for future in as_completed(futures):
        result = future.result()
        if result:
            category, data_EI, data_F = result
            if category == 'pet':
                pet_data_EI.append(data_EI)
                pet_data_F.append(data_F)
            elif category == 'short':
                short_data_EI.append(data_EI)
                short_data_F.append(data_F)
            elif category == 'long':
                long_data_EI.append(data_EI)
                long_data_F.append(data_F)

# Sort the data by length for plotting
pet_data_EI.sort(key=lambda x: x[0])
short_data_EI.sort(key=lambda x: x[0])
long_data_EI.sort(key=lambda x: x[0])

pet_data_F.sort(key=lambda x: x[0])
short_data_F.sort(key=lambda x: x[0])
long_data_F.sort(key=lambda x: x[0])

# Normalize the data
solid_beam_EI = (962.8 / 12.0 * (4.40908153701)**4) / 1000.0**2
solid_beam_f = solid_beam_EI * 3 / (100.0 * pet_data_F[-1][0]**2)

pet_data_EI = [(x[0] / pet_data_EI[0][0], x[1] / solid_beam_EI) for x in pet_data_EI]
short_data_EI = [(x[0] / short_data_EI[0][0], x[1] / solid_beam_EI) for x in short_data_EI]
long_data_EI = [(x[0] / long_data_EI[0][0], x[1] / solid_beam_EI) for x in long_data_EI]

pet_data_F = [(x[0] / pet_data_F[0][0], x[1]) for x in pet_data_F]
short_data_F = [(x[0] / short_data_F[0][0], x[1]) for x in short_data_F]
long_data_F = [(x[0] / long_data_F[0][0], x[1]) for x in long_data_F]

# Calculate the percentage improvement at 100% deployment
pet_ei_at_100 = pet_data_EI[-1][1]
short_ei_at_100 = short_data_EI[-1][1]
long_ei_at_100 = long_data_EI[-1][1]

short_improvement_pct = (short_ei_at_100 - 1.0) / 1.0 * 100
long_improvement_pct = (-long_ei_at_100 + solid_beam_EI) / long_ei_at_100 * 100

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(*zip(*pet_data_EI), '-', color='#69DFE8', label='PET', linewidth=4.0)
plt.plot(*zip(*short_data_EI), '-', color='#EBAD4B', label='Short-Link Scissor', linewidth=4.0)
plt.plot(*zip(*long_data_EI), '-', color='#963800', label='Long-Link Scissor', linewidth=4.0)
plt.plot([pet_data_EI[0][0], pet_data_EI[-1][0]], [1.0, 1.0], '--', color='#6A4E72', label='Solid Beam', linewidth=2.0)

plt.legend()
plt.xlabel('Extension Ratio')
plt.ylabel('Normalized Flexural Modulus')
plt.grid(False)

# Save the plot with a timestamp
now = pd.Timestamp("now")
plt.savefig(f'data/plots/deployment_test/{now}_DL_vs_EI_comp_srt_imp_pct_{short_improvement_pct:.2f}_lng_{long_improvement_pct:.2f}.svg', format='svg')
