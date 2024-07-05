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

# Configuration dictionary
config = {
    "tests": ["cant_x", "compression", "torsion", "tension"],
    "normalize_mass": [True, False],
    "directory": "data/paper_results/extension_ratio_sweep",
    "mass_data_dir": "data/models"
}

def read_mass_file(material):
    """
    Reads the mass data for a given material.

    Args:
        material (str): The material name.

    Returns:
        pd.DataFrame: DataFrame containing the mass data.
    """
    filepath = os.path.join(config['mass_data_dir'], material, 'extension_ratio_sweep', 'mass.csv')
    return pd.read_csv(filepath)

def check_mass_file(filepath, test_type, mass_data):
    """
    Checks if the mass data is available for a given file and test type.

    Args:
        filepath (str): Path to the CSV file.
        test_type (str): The type of test.
        mass_data (pd.DataFrame): DataFrame containing the mass data.

    Returns:
        float: The mass if available, else False.
    """
    processed_filename = os.path.basename(filepath).replace("_" + test_type, '')
    if (mass_data['filename'] == processed_filename).any():
        return mass_data.loc[mass_data['filename'] == processed_filename, 'mass'].iloc[0]
    else:
        return False

def process_file(filepath, test_type, normalize):
    """
    Processes each CSV file to extract relevant data.

    Args:
        filepath (str): Path to the CSV file.
        test_type (str): The type of test.
        normalize (bool): Whether to normalize the results by mass.

    Returns:
        tuple: A tuple containing the category (str) and EI data (tuple).
    """
    try:
        df = pd.read_csv(filepath)

        # Extract data
        ind = len(df['FX']) - 1
        length = df['L'][ind]
        displacement = df['Displacement'][ind]
        
        fx, fy, fz = df['FX'][ind], df['FY'][ind], df['FZ'][ind]
        f = max(abs(fx), abs(fy), abs(fz))
        f = np.nan_to_num(f, nan=0.0)
        
        mx, my, mz = df['MX'][ind], df['MY'][ind], df['MZ'][ind]
        m = max(abs(mx), abs(my), abs(mz))
        m = np.nan_to_num(m, nan=0.0)
        
        if "HERDS" in filepath:
            thickness = float(re.search(r't_([0-9.]+)_', os.path.basename(filepath)).group(1))
            n_cells = float(re.search(r'cells_([0-9.]+)_', os.path.basename(filepath)).group(1))
            material = "herds"
            test_type += "_kres"
            initial_height = n_cells * 4.0 * thickness
                
        elif "kres" in filepath or "radius" in filepath:
            thickness = float(re.search(r'thickness_([0-9.]+)_', os.path.basename(filepath)).group(1))
            n_cells = 3.0
            material = "kresling"
            test_type += "_kres"
            initial_height = n_cells * 2.0 * thickness
            
        elif "pet" in filepath or "width" in filepath:
            alpha = float(re.search(r'alpha_([0-9.]+)_', os.path.basename(filepath)).group(1))
            thickness = float(re.search(r't_([0-9.]+)_', os.path.basename(filepath)).group(1))
            n_cells = float(re.search(r'cells_([0-9.]+)_', os.path.basename(filepath)).group(1))
            material = "pets"
            initial_height = n_cells * 2.0 * thickness
        
        # Get mass data
        mass = 1.0  # default mass value if normalization is False
        if normalize:
            mass_data = read_mass_file(material)
            mass = check_mass_file(filepath, test_type, mass_data)
            if not mass:
                return None
                
        # Calculate EI based on test_type
        if 'cant_x' in test_type:
            scale = 1000.0**2
            EI = length**3 * f / (3.0 * displacement)
        elif 'compression' in test_type:
            scale = 1.0
            EI = f / (displacement / 1000.0)
        elif 'torsion' in test_type:
            scale = 1.0
            EI = m / displacement
        elif 'tension' in test_type:
            scale = 1.0
            EI = f / (displacement / 1000.0)
                    
        data_point_EI = (length / initial_height, EI / scale / mass)
        return material, data_point_EI

    except:
        return None

def plot_results(pet_data, kres_data, herds_data, test_type, normalize):
    """
    Plots the results.

    Args:
        pet_data (list): List of PET data points.
        kres_data (list): List of KRES data points.
        herds_data (list): List of HERDS data points.
        test_type (str): The type of test.
        normalize (bool): Whether the results are normalized by mass.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(*zip(*pet_data), 'o', ms=7, color='#69DFE8', mfc="white", mec='#69DFE8', label='PET', linewidth=2.0)
    plt.plot(*zip(*kres_data), 'o', ms=7, color='#EBAD4B', mfc="white", mec='#EBAD4B', label='KRES', linewidth=2.0)
    plt.plot(*zip(*herds_data), 'o', ms=7, color='#963800', mfc="white", mec='#963800', label='HERDS', linewidth=2.0)
    plt.yscale('log')
    plt.xlim([0, 250])
    plt.minorticks_on()
    plt.legend()
    plt.xlabel('Extension Ratio')
    
    ylabel_map = {
        'cant_x': 'Flexural Modulus (EI)',
        'compression': 'Compressive Stiffness',
        'torsion': 'Torsional Stiffness',
        'tension': 'Tensile Stiffness'
    }
    
    if normalize:
        plt.ylabel(fr"{ylabel_map[test_type]} per Mass $[\frac{{N}}{{m^2*kg}}]$")
    else:
        plt.ylabel(fr"{ylabel_map[test_type]} $[\frac{{N}}{{m^2}}]$")
    
    plt.grid(True)
    now = pd.Timestamp("now")
    path = "data/plots/extension_ratio_sweep"
    if not os.path.exists(path):
        os.makedirs(path)
    plt.savefig(f'{path}/{now}_{test_type}_mass_norm_{str(normalize)}.svg', format='svg')

def main():
    for test_type in config["tests"]:
        for normalize in config["normalize_mass"]:
            pet_data_EI = []
            kres_data_EI = []
            herds_data_EI = []
            
            file_pattern = f"*{test_type}*"
            filepaths = glob.glob(os.path.join(config['directory'], file_pattern))
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = [executor.submit(process_file, filepath, test_type, normalize) for filepath in filepaths]
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        category, data_EI = result
                        if category == 'pets':
                            pet_data_EI.append(data_EI)
                        elif category == 'kresling':
                            kres_data_EI.append(data_EI)
                        elif category == 'herds':
                            herds_data_EI.append(data_EI)
           
            # Sort the data by length for plotting
            pet_data_EI.sort(key=lambda x: x[0])
            kres_data_EI.sort(key=lambda x: x[0])
            herds_data_EI.sort(key=lambda x: x[0])
            
            plot_results(pet_data_EI, kres_data_EI, herds_data_EI, test_type, normalize)

if __name__ == "__main__":
    main()
