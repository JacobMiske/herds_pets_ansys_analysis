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
directory = "data/paper_results/aspect_ratio_scaling"

# Initialize the plots
plt.figure(figsize=(10, 6))
pet_data_EI = []

def process_file(filepath):
    """
    Process each CSV file to extract relevant data.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        tuple: A tuple containing the category (str), EI data (tuple), and force data (tuple).
    """
    df = pd.read_csv(filepath)
    width = 1.8
    alpha = re.search(r'alpha_([0-9.]+)_', os.path.basename(filepath)).group(1)
    member_scale = float(re.search(r'scale_([0-9.]+)_', os.path.basename(filepath)).group(1))
    l1_length = 34.32 * member_scale

    scale = 1000.0**2
    ind = len(df['FX']) - 1

    length = df['L'][ind]
    displacement = df['Displacement'][ind]
    fx, fy, fz = df['FX'][ind], df['FY'][ind], df['FZ'][ind]
    f = max(abs(fx), abs(fy), abs(fz))
    EI = length**3 * f / (3.0 * displacement)

    data_point_EI = (l1_length / width, EI / scale)
    data_point_F = (l1_length / width, f)

    if "l1" in filepath:
        return ('pet', data_point_EI, data_point_F)

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

# Sort the data by length for plotting
pet_data_EI.sort(key=lambda x: x[0])

# Normalize the data
solid_beam_EI = (962.8 / 12.0 * (4.40908153701)**4) / 1000.0**2
pet_data_EI = [(x[0], x[1] / solid_beam_EI) for x in pet_data_EI]

# Get max pet data
pet_ei_at_100 = pet_data_EI[-1][1]

# Find the first index where pet data > 1.0
# first_index = next((i for i, x in enumerate(pet_data_EI) if x[1] > 1.0), None)
# print(f'first index where pet data > 1.0: {first_index}')
# print(f'pet data at first index: {pet_data_EI[first_index]}')

# Plotting
plt.plot(*zip(*pet_data_EI), '-', color='#69DFE8', label='PET', linewidth=4.0)
plt.plot([pet_data_EI[0][0], pet_data_EI[-1][0]], [1.0, 1.0], '--', color='#6A4E72', label='Solid Beam', linewidth=2.0)

plt.legend()
plt.xlabel('Short-Link Scissor Member Aspect Ratio')
plt.ylabel('Normalized Flexural Modulus')
plt.grid(False)

# Save the plot with a timestamp
now = pd.Timestamp("now")
plt.savefig(f'data/plots/aspect_ratio_scaling/{now}_DL_vs_EI_comp_imp_pct_{pet_ei_at_100:.2f}.svg', format='svg')
