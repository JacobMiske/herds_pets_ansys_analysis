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
        "mech_type": "",
        "boundary_condition_function": "", # change to different boundary condition function
        "percent_displacement": 1.0,
        "substeps": 10,
        "num_elements": 10,
        "num_cross_elements": 3,
        "element_type": "BEAM188",
        "result_filename": None,
        "scale": 1.0,
        "cross_scale": 1.0,
        "E": 2.1e5,
        "fixed_displacement": None,
        "warp": False,
    }
    
    folder_paths = ["data/models/pets/extension_ratio_sweep", "data/models/kresling/extension_ratio_sweep", "data/models/herds/extensions_ratio_sweep"]
    mech_types = ["PET", "KRESLING", "HERDS"]
    boundary_condition_functions = ["cant_x", "compression", "tension", "torsion"]
    
    for folder_path, mech_type in zip(folder_paths, mech_types):
        filenames = os.listdir(folder_path)
        for filename in filenames:
            if "mass" in filename:
                continue
            for boundary_condition_function in boundary_condition_functions:
                if mech_type == "KRESLING" or mech_type == "HERDS":
                    boundary_condition_function = boundary_condition_function + "_kres"
                    
                simulation_args["boundary_condition_function"] = boundary_condition_function
                simulation_args["filename"] = filename
                simulation_args["folder_path"] = folder_path
                simulation_args["mech_type"] = mech_type
                simulation_args["fixed_displacement"] = None
                
                if boundary_condition_function == "torsion":
                    simulation_args["fixed_displacement"] = 0.0628
                    
                run_simulation_with_timeout(simulation_args)

if __name__ == "__main__":
    main()