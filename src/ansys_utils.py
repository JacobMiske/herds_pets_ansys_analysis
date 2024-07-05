from ansys.mapdl import core as pymapdl
from boundary_conditions import get_displacement
from model_utils import find_bounds
import logging
import csv 
import numpy as np

def launch_mapdl(nproc=2, mode="grpc", loglevel="ERROR", log_apdl="", run_location=""):
    """
    Launches an instance of MAPDL (Mechanical APDL) using the specified parameters.

    Parameters:
        nproc (int): Number of processors to use (default is 2).
        mode (str): Connection mode to use, either "grpc" or "corba" (default is "grpc").
        loglevel (str): Log level for MAPDL messages, options are "ERROR", "WARNING", "INFO", "DEBUG" (default is "ERROR").
        log_apdl (str): File path to save the APDL log (default is "pymapdl_log.txt").
        run_location (str): Directory path where MAPDL will run (default is current working directory).

    Returns:
        mapdl (pymapdl.Mapdl): Instance of the MAPDL class.
    """
    mapdl = pymapdl.launch_mapdl(nproc=nproc, mode=mode, loglevel=loglevel, log_apdl=log_apdl, run_location=run_location, start_timeout=600.0, override=True)
    return mapdl

def define_material(mapdl, units="SI", E=2.1e5, nu=0.3, rho=7800.0):
    """
    Defines the material properties in the ANSYS MAPDL environment.

    Parameters:
        mapdl (object): The ANSYS MAPDL object.
        units (str): The unit system to be used. Default is "SI".
        E (float): The elastic modulus of the material. Default is 2.1e5 MPa.
        nu (float): The Poisson's ratio of the material. Default is 0.3.
        rho (float): The density of the material. Default is 7800 kg/m^3.
    """
    logging.info('defining material properties')

    mapdl.prep7()  # set solver to a good processor for materials
    # This example will use SI units.
    # mapdl.units(label=units)  # SI - International system (m, kg, s, K).
    # Define a material (nominal steel in SI)
    mapdl.mp("EX", 1, E)  # Elastic moduli in MPa (kg/(m*s**2))
    mapdl.mp("DENS", 1, rho)  # Density in kg/m3
    mapdl.mp("NUXY", 1, nu)  # Poisson's Ratio
    
def run_solve(mapdl, large_deformation="ON", substeps=100):
    """
    Runs the solution process for the given MAPDL instance.

    Parameters:
    - mapdl (MAPDL): The MAPDL instance to run the solution on.
    - large_deformation (str, optional): Specifies whether to enable large deformation effects. Defaults to "ON".
    - subStep (int, optional): The number of substeps to use in the solution process. Defaults to 10.
    - maxStep (int, optional): The maximum number of steps to perform in the solution process. Defaults to 100.
    - minStep (int, optional): The minimum number of steps to perform in the solution process. Defaults to 2.
    """

    #* Solve
    mapdl.allsel()

    #* set the processor
    logging.info('Solving')

    #* Enable large deformation effects
    mapdl.nlgeom(large_deformation)

    #* Set the number of substeps
    # NSUBST, Nsub, Nsubmax, Nsubmin
    mapdl.nsubst(nsbstp=substeps, nsbmn=substeps, nsbmx=10*substeps)

    #* Number of equalibrium solves
    mapdl.neqit(neqit=1000)
    # mapdl.lnsrch('ON') # Line Search
    # mapdl.nropt("FULL") #full newton raphson
    
    #* Save results for all nodes and elements
    mapdl.outres('ALL', 'LAST')  
    
    #* Solve the system
    output = mapdl.solve(verbose=False)
    mapdl.finish()
    logging.debug(output)

    # print("Finished Solving")
    logging.info('Finished Solving')

def write_to_csv(filename, data, displacement_type):
    """Writes the collected data to a CSV file."""
    headers = ['Displacement', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ', 'L'] #+ (['L', 'EI'] if "bending" in displacement_type else ['L', 'EA'])
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(data)
    
def post_process(mapdl, percent_displacement, substeps, filename, displacement_type, mech_type, fixed_displacement=None, plot=False):
    """
    Perform post-processing on the results obtained from ANSYS Mechanical APDL.

    Parameters:
    - mapdl (MAPDL): An instance of the MAPDL class representing the ANSYS Mechanical APDL environment.
    - displacement (float): The total displacement value.
    - substeps (int): The number of substeps.
    - filename (str): The name of the CSV file to write the results to.
    - plot (bool, optional): Flag indicating whether to plot the results. Defaults to False.

    Returns:
    - reaction_forces (dict): A dictionary containing the reaction forces at the fixed support.

    """
    logging.info("post_process")
    # print("Post Processing")
    xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd =find_bounds(mapdl)  
    displacement = fixed_displacement if fixed_displacement is not None else get_displacement(mapdl, mech_type, percent_displacement)  

    if mech_type == "KRESLING" or mech_type == "HERDS":
        length = ymax - ymin
    else:
        length = ymax_2nd - ymin_2nd

    # Post-processing
    mapdl.post1()  # Enter post-processing

    data_to_write = []
    
    mapdl.set('LAST')
    mapdl.cmsel('S', 'driven')

    if not mapdl.solution.converged:
        # print("FAILED TO CONVERGE")
        fx = fy = fz = mx = my = mz = np.nan
        data_to_write.append([displacement, fx, fy, fz, mx, my, mz, length])
        write_to_csv(filename, data_to_write, displacement_type)
        return False
    
    mapdl.fsum()
    fx = mapdl.get(entity='FSUM', item1='ITEM', it1num='FX')
    fy = mapdl.get(entity='FSUM', item1='ITEM', it1num='FY')
    fz = mapdl.get(entity='FSUM', item1='ITEM', it1num='FZ')
    mx = mapdl.get(entity='FSUM', item1='ITEM', it1num='MX')
    my = mapdl.get(entity='FSUM', item1='ITEM', it1num='MY')
    mz = mapdl.get(entity='FSUM', item1='ITEM', it1num='MZ')   
    
    data_row = [displacement, fx, fy, fz, mx, my, mz, length]
    
    data_to_write.append(data_row)
            
    write_to_csv(filename, data_to_write, displacement_type)
    return True
   