import sys
import os

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '../../src'))
sys.path.append(src_dir)

from run_ansys_simulation import run_simulation_with_timeout

def main():
    simulation_args = {
        "filename": "",
        "folder_path": "",
        "mech_type": "PET",
        "boundary_condition_function": "cant_x",
        "percent_displacement": 1.0,
        "substeps": 100,
        "num_elements": 10,
        "num_cross_elements": 3,
        "element_type": "BEAM188",
        "result_filename": None,
        "scale": 5.0,
        "cross_scale": 0.6,
        "E": 962.8,
        "fixed_displacement": None,
        "warp": False,
    }
    
    folder_paths = ["data/models/pets/deployment_test", "data/models/short_scissor/deployment_test", "data/models/long_scissor/deployment_test"]
    mech_types = ["PET", "SCISSOR", "SCISSOR"]
    
    for folder_path, mech_type in zip(folder_paths, mech_types):
        filenames = os.listdir(folder_path)
        for filename in filenames:
            print(filename)
            if "mass" in filename:
                continue
            
            simulation_args["filename"] = filename
            simulation_args["folder_path"] = folder_path
            simulation_args["mech_type"] = mech_type
            run_simulation_with_timeout(simulation_args)

if __name__ == "__main__":
    main()
