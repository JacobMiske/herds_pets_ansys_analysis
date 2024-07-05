import argparse

def create_parser():
    """
    Creates an argument parser for the simulation setup and execution.

    Returns:
    - argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description='Simulation setup and execution.')

    # Required arguments
    parser.add_argument('filename', type=str, help='Name of the file containing the geometry.')
    parser.add_argument('folder_path', type=str, help='Path to the folder containing the geometry file.')
    parser.add_argument('boundary_condition_function', type=str, help='Name of the function to set up boundary conditions.')
    parser.add_argument('--mech_type', type=str, help='Mechanical type of the material.')


    # Optional arguments
    parser.add_argument('--percent_displacement', type=float, help='Percent displacement of the tip of the body.', default=1.0)
    parser.add_argument('--fixed_displacement', type=float, help='Fixed Displacement of the tip of the body.', default=None)
    parser.add_argument('--substeps', type=int, help='Number of substeps to use in the simulation.', default=10)
    parser.add_argument('--num_elements', type=int, help='Number of elements in the mesh.', default=10)
    parser.add_argument('--num_cross_elements', type=int, help='Number of cross-sectional elements in the mesh.', default=3)
    parser.add_argument('--element_type', type=str, help='Type of element to use in the simulation.', default="BEAM188")
    parser.add_argument('--result_filename', type=str, help='Name of the output file.', default=None)
    parser.add_argument('--scale', type=float, help='Scale of the geometry.', default=1.0)
    parser.add_argument('--cross_scale', type=float, help='Cross-sectional scale of the geometry.', default=1.0)
    parser.add_argument('--E', type=float, help='Young\'s Modulus of the material.', default=962.8)
    parser.add_argument('--warp', action='store_true', help='Enable warping of the geometry.')

    
    return parser
