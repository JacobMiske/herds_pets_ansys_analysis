import logging
import inspect
import pandas as pd
import os
import re
from datetime import datetime

def save_values_to_csv(filename, data_dict):
    """
    Saves a dictionary of values to a CSV file.
    
    Parameters:
    - filename (str): The path to the output CSV file.
    - data_dict (dict): The dictionary of values to save.
    """
    df = pd.DataFrame(data_dict, index=[0])
    df.to_csv(filename, index=False)

def delete_non_cdb_files(directory):
    """
    Deletes all files in the specified directory and its subdirectories,
    except those with the .cdb extension.
    
    Parameters:
    - directory (str): The path to the directory.
    """
    for root, _, files in os.walk(directory, topdown=False):
        for name in files:
            if name in {"run.log", "file.rst"} or ".cdb" in name:
                continue
            file_path = os.path.join(root, name)
            os.remove(file_path)

def save_bc_to_csv(filename, bc_dir, boundary_condition_function, boundary_condition_function_exec):
    """
    Saves the boundary condition function parameters to a CSV file.
    
    Parameters:
    - filename (str): The base filename for the CSV file.
    - bc_dir (str): The directory where the CSV file will be saved.
    - boundary_condition_function (str): The name of the boundary condition function.
    - boundary_condition_function_exec (function): The boundary condition function.
    """
    # Get the inputs to boundary_condition_function and save to CSV
    bc_params = inspect.signature(boundary_condition_function_exec).parameters
    bc_params = {k: v.default if v.default is not inspect.Parameter.empty else None for k, v in bc_params.items()}
    bc_params["boundary_condition_function"] = boundary_condition_function
    
    save_values_to_csv(filename=os.path.join(bc_dir, f"{filename}_{boundary_condition_function}.csv"), data_dict=bc_params)

def init_logging(filename, folder_path, result_filename, boundary_condition_function):
    """
    Initializes logging and creates necessary directories.
    
    Parameters:
    - filename (str): The name of the file containing the geometry.
    - folder_path (str): The path to the folder containing the file.
    - result_filename (str): The name of the output file.
    - boundary_condition_function (str): The name of the boundary condition function.
    
    Returns:
    - log_dir (str): The directory where logs are stored.
    - output_dir (str): The directory where results are stored.
    - config_path (str): The path to the configuration file.
    - result_filename (str): The full path to the result file.
    - output_filename (str): The base name for output files.
    """
    # Separate filename and file_extension based on '.'
    filename, file_extension = os.path.splitext(filename)
    file_extension = file_extension[1:]
  
    # Get the folder_name from the folder_path
    folder_name = os.path.basename(folder_path)
    
    # Get the current date and time
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M_")
    
    output_filename = f"{timestamp}_{folder_name}_{boundary_condition_function}_{filename}"
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join("log", output_filename)
    os.makedirs(log_dir, exist_ok=True)
        
    logging.basicConfig(filename=os.path.join(log_dir, 'run.log'), level=logging.DEBUG)

    # Create output directory if it doesn't exist
    output_dir = os.path.join("data/results", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # Get the path to the geometry
    config_path = os.path.join(folder_path, f"{filename}.{file_extension}")
    logging.info(f"config_path: {config_path}")
    
    if result_filename:
        result_filename = os.path.join(output_dir, f"{result_filename}.csv")
    else:
        result_filename = os.path.join(output_dir, f"{filename}_{boundary_condition_function}.csv")

    return log_dir, config_path, result_filename 
