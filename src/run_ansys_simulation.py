from ansys_utils import launch_mapdl, define_material, run_solve, post_process
from model_utils import get_beam_model_new
from boundary_conditions import *
from parser_utils import create_parser
from logging_utils import init_logging, delete_non_cdb_files
import os
from multiprocessing import Process, Queue
import gc

def run_simulation_with_timeout(simulation_vars, timeout=1800):
    """
    Runs the simulation in a separate process with a timeout.

    Args:
        simulation_vars (dict): Dictionary containing the simulation parameters.

    Returns:
        The result of the simulation or None if the process times out.
    """
    def target(queue):
        result = run_simulation(**simulation_vars)
        queue.put(result)

    queue = Queue()
    p = Process(target=target, args=(queue,))
    p.start()
    p.join(timeout=timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        print("Simulation terminated due to timeout.")
        queue.close()
        queue.join_thread()
        del queue
        gc.collect()
        return None
    else:
        result = queue.get()
        queue.close()
        queue.join_thread()
        del queue
        gc.collect()
        return result
        

def run_simulation(filename, folder_path, mech_type, boundary_condition_function, percent_displacement=1.0, substeps=10, num_elements=20, num_cross_elements=10, element_type="BEAM188", result_filename=None, scale=1.0, cross_scale=0.6, E=962.8, fixed_displacement=None, warp=False):
    """
    Runs a simulation using Ansys software.

    Args:
        filename (str): The name of the file containing the geometry.
        folder_path (str): The path to the folder containing the file.
        mech_type (str): The type of mechanism to analyze.
        boundary_condition_function (str): The name of the function that sets up the boundary conditions.
        percent_displacement (float): The percentage of displacement to apply. Default is 1.0.
        substeps (int): Number of substeps to use in the simulation. Default is 10.
        num_elements (int): Number of elements in the mesh. Default is 20.
        num_cross_elements (int): Number of cross-sectional elements in the mesh. Default is 10.
        element_type (str): Type of element to use in the simulation. Default is "BEAM188".
        result_filename (str): Name of the output file. Default is None.
        scale (float): Scale of the geometry. Default is 1.0.
        cross_scale (float): Cross-sectional scale of the geometry. Default is 0.6.
        E (float): Young's Modulus of the material. Default is 962.8.
        fixed_displacement (float): Fixed displacement to apply. Default is None.
        warp (bool): Enable warping of the geometry. Default is False.

    Returns:
        The result of the post-processing step.
    """
    log_dir, config_path, result_filename = init_logging(filename, folder_path, result_filename, boundary_condition_function)
    
    nproc = 12  # Number of processes to use
    mapdl = launch_mapdl(nproc=nproc, run_location=log_dir)
    
    # Define the material properties
    define_material(mapdl, E=E)
    get_beam_model_new(mapdl, config_path, element_type=element_type, ndiv=num_elements, num_cross_elements=num_cross_elements, scale=scale, cross_scale=cross_scale, warp=warp, mech_type=mech_type)
    
    # Execute the boundary condition function
    boundary_condition_function_exec = globals()[boundary_condition_function]
    boundary_condition_function_exec(mapdl, percent_displacement=percent_displacement, mech_type=mech_type, fixed_displacement=fixed_displacement)
    
    # Run the solution process
    run_solve(mapdl, substeps=substeps)
    
    # Post-process the results
    solved = post_process(mapdl, percent_displacement, substeps, result_filename, boundary_condition_function, mech_type, fixed_displacement=fixed_displacement)
    
    # Delete non-CDB files
    delete_non_cdb_files(log_dir)
    
    # Close the MAPDL instance
    mapdl.exit()
    
    return solved

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    simulation_args = vars(args)

    try:
        result = run_simulation_with_timeout(simulation_args)
        if result is not None:
            print("Simulation completed successfully.")
        else:
            print("Simulation did not complete within the timeout period.")
    except Exception as e:
        print(f"An error occurred during the simulation: {e}")
