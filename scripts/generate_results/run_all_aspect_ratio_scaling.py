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
        "substeps": 10,
        "num_elements": 10,
        "num_cross_elements": 3,
        "element_type": "BEAM188",
        "result_filename": None,
        "scale": 1.0,
        "cross_scale": 1.0,
        "E": 962.8,
        "fixed_displacement": None,
        "warp": False,
    }
    
    folder_paths = ["data/models/pets/aspect_ratio_scaling"]
    
    for folder_path in folder_paths:
        filenames = os.listdir(folder_path)
        for filename in filenames:
            print(filename)
            if "mass" in filename:
                continue
            
            simulation_args["filename"] = filename
            simulation_args["folder_path"] = folder_path
            run_simulation_with_timeout(simulation_args)


if __name__ == "__main__":
    main()