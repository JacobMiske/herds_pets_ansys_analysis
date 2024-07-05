import logging
from model_utils import find_bounds
import numpy as np

def apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, boundary_type, driven_constraints, fixed_constraints={'UX': 0, 'UY': 0, 'UZ': 0}):
    """
    General function to apply boundary conditions for different analysis types.
    
    Parameters:
    - mapdl: An instance of the MAPDL class.
    - mech_type: A string indicating the type of mechanism to analyze.
    - percent_displacement: A float indicating the percentage of displacement to apply.
    - fixed_displacement: A float indicating the fixed displacement to apply.
    - boundary_type: A string indicating the type of boundary condition.
    - driven_constraints: A dictionary of constraints to apply to the driven nodes.
    - fixed_constraints: A dictionary of constraints to apply to the fixed nodes. Default is {'UX': 0, 'UY': 0, 'UZ': 0}.
    
    Returns:
    None
    """
    logging.info(f"{boundary_type}_boundary_conditions")
    mapdl.slashsolu()
    mapdl.antype("STATIC")
    
    displacement = fixed_displacement if fixed_displacement is not None else get_displacement(mapdl, mech_type, percent_displacement)
    
    xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd = find_bounds(mapdl)
    
    if boundary_type in ['compression', 'tension']:
        select_and_fix_nodes(mapdl, 'fixed', y_range=(ymin, ymin), constraints=fixed_constraints)
        select_and_fix_nodes(mapdl, 'driven', y_range=(ymax, ymax), constraints=driven_constraints(displacement))
    elif boundary_type in ['cant_x', 'cant_z']:
        select_and_fix_nodes(mapdl, 'fixed', y_range=(ymax, ymax), constraints=fixed_constraints)
        select_and_fix_nodes(mapdl, 'driven', y_range=(ymin, ymin), x_range=(xmax, xmax), constraints=driven_constraints(displacement))
    elif boundary_type == 'torsion':
        select_and_fix_nodes(mapdl, 'fixed', y_range=(ymin, ymin), constraints=fixed_constraints)
        select_and_fix_nodes(mapdl, 'driven', y_range=(ymax, ymax), constraints=driven_constraints(displacement))
    
    mapdl.allsel()
    
def apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, boundary_type, driven_constraints, fixed_constraints={'UX': 0, 'UY': 0, 'UZ': 0}):
    """
    General function to apply boundary conditions for different analysis types for areas.
    
    Parameters:
    - mapdl: An instance of the MAPDL class.
    - mech_type: A string indicating the type of mechanism to analyze.
    - percent_displacement: A float indicating the percentage of displacement to apply.
    - fixed_displacement: A float indicating the fixed displacement to apply.
    - boundary_type: A string indicating the type of boundary condition.
    - driven_constraints: A dictionary of constraints to apply to the driven nodes.
    - fixed_constraints: A dictionary of constraints to apply to the fixed nodes. Default is {'UX': 0, 'UY': 0, 'UZ': 0}.
    
    Returns:
    None
    """
    logging.info(f"{boundary_type}_boundary_conditions")
    mapdl.slashsolu()
    mapdl.antype("STATIC")
    
    displacement = fixed_displacement if fixed_displacement is not None else get_displacement(mapdl, mech_type, percent_displacement)
    
    xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd = find_bounds(mapdl)
    
    if boundary_type in ['compression', 'tension']:
        select_and_fix_areas(mapdl, 'fixed', y_range=(ymin, ymin_2nd), constraints=fixed_constraints)
        select_and_fix_areas(mapdl, 'driven', y_range=(ymax_2nd, ymax), constraints=driven_constraints(displacement))
    elif boundary_type in ['cant_x', 'cant_z']:
        select_and_fix_areas(mapdl, 'fixed', y_range=(ymin, ymin_2nd), constraints=fixed_constraints)
        select_and_fix_nodes(mapdl, 'driven', y_range=(ymax, ymax), x_range=(xmax, xmax), constraints=driven_constraints(displacement))
    elif boundary_type == 'torsion':
        select_and_fix_areas(mapdl, 'fixed', y_range=(ymin, ymin_2nd), constraints=fixed_constraints)
        select_and_fix_nodes(mapdl, 'driven', y_range=(ymax_2nd, ymax), constraints=driven_constraints(displacement))
    
    mapdl.allsel()

def get_displacement(mapdl, mech_type, percent_displacement=1.0):
    mapdl.allsel()

    xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd =find_bounds(mapdl) 
    
    # displacement = (ymax-ymin)*percent_displacement/100.0
    # if mech_type == "PET":
    # import pdb; pdb.set_trace()
    if mech_type == "HERDS" or mech_type == "KRESLING":
        displacement = (ymax-ymin)*percent_displacement/100.0
    else:
        length = ymax_2nd - ymin_2nd
        displacement = length*percent_displacement/100.0 
        
    return displacement

def select_and_fix_nodes(mapdl, location, y_range, z_range=None, x_range=None, constraints=None):
    """General function to select nodes based on location and apply constraints with optional displacement values.

    Args:
        mapdl: The ANSYS MAPDL object.
        location: Name for the node component list.
        y_range: The Y range (min, max) to select nodes.
        z_range: The Z range (min, max) to select nodes, None to skip Z selection.
        x_range: The X range (min, max) to select nodes, None to skip X selection.
        constraints: Dictionary of constraints where keys are 'UX', 'UY', 'UZ', 'ROTX', 'ROTY', 'ROTZ'
                     and values are the displacement values for each.
    """
    mapdl.seltol(1e-8) # Note add more nodes were added than sometimes ansys would grab additional nodes by accident
    if z_range is not None:
        node_ids = mapdl.nsel('S', 'LOC', 'Z', *z_range)
        if x_range is not None:
            node_ids = mapdl.nsel('R', 'LOC', 'X', *x_range)
    elif x_range is not None:
        node_ids = mapdl.nsel('S', 'LOC', 'X', *x_range)
        
    if x_range is None and z_range is None:
        node_ids = mapdl.nsel('S', 'LOC', 'Y', *y_range)
    else:
        node_ids = mapdl.nsel('R', 'LOC', 'Y', *y_range)

    # print(f"{location} node ids: {node_ids}")
    mapdl.cm(location, 'NODE')

    # Apply constraints and displacements as specified
    if constraints:
        for constraint, value in constraints.items():
            if constraint in ['UX', 'UY', 'UZ', 'ROTX', 'ROTY', 'ROTZ']:
                mapdl.d('ALL', constraint, value)

    # print(f"{location} node ids updated with constraints: {constraints}")

def select_and_fix_areas(mapdl, location, y_range, z_range=None, x_range=None, constraints=None):
    """General function to select nodes based on location and apply constraints with optional displacement values.

    Args:
        mapdl: The ANSYS MAPDL object.
        location: Name for the node component list.
        y_range: The Y range (min, max) to select nodes.
        z_range: The Z range (min, max) to select nodes, None to skip Z selection.
        x_range: The X range (min, max) to select nodes, None to skip X selection.
        constraints: Dictionary of constraints where keys are 'UX', 'UY', 'UZ', 'ROTX', 'ROTY', 'ROTZ'
                     and values are the displacement values for each.
    """
    if z_range is not None:
        node_ids = mapdl.asel('S', 'LOC', 'Z', *z_range)
        if x_range is not None:
            node_ids = mapdl.asel('R', 'LOC', 'X', *x_range)
    if x_range is not None:
        node_ids = mapdl.asel('S', 'LOC', 'X', *x_range)
        
    if x_range is None and z_range is None:
        node_ids = mapdl.asel('S', 'LOC', 'Y', *y_range)
    else:
        node_ids = mapdl.asel('R', 'LOC', 'Y', *y_range)

    # print(f"{location} area ids: {node_ids}")
    mapdl.cm(location, 'AREA')

    # Apply constraints and displacements as specified
    if constraints:
        for constraint, value in constraints.items():
            if constraint in ['UX', 'UY', 'UZ', 'ROTX', 'ROTY', 'ROTZ']:
                mapdl.da('ALL', constraint, value)

    # print(f"{location} area ids updated with constraints: {constraints}")

def compression_kres(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, 'compression',
                              driven_constraints=lambda d: {'UX': 0, 'UY': -d, 'UZ': 0})

def tension_kres(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, 'tension',
                              driven_constraints=lambda d: {'UX': 0, 'UY': d, 'UZ': 0})

def cant_x_kres(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, 'cant_x',
                              driven_constraints=lambda d: {'UX': -d, 'UZ': 0})

def cant_z_kres(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, 'cant_z',
                              driven_constraints=lambda d: {'UZ': -d, 'UX': 0})

def torsion_kres(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions(mapdl, mech_type, percent_displacement, fixed_displacement, 'torsion',
                              driven_constraints=lambda d: {'UX': 0, 'UY': 0, 'UZ': 0, 'ROTX': 0, 'ROTY': d, 'ROTZ': 0},
                              fixed_constraints={'UX': 0, 'UY': 0, 'UZ': 0, 'ROTX': 0, 'ROTY': 0, 'ROTZ': 0})

def compression(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, 'compression',
                                    driven_constraints=lambda d: {'UX': 0, 'UY': -d, 'UZ': 0})

def tension(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, 'tension',
                                    driven_constraints=lambda d: {'UX': 0, 'UY': d, 'UZ': 0})

def cant_x(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, 'cant_x',
                                    driven_constraints=lambda d: {'UX': -d, 'UZ': 0})

def cant_z(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, 'cant_z',
                                    driven_constraints=lambda d: {'UZ': -d, 'UX': 0})

def torsion(mapdl, mech_type, percent_displacement=1.0, fixed_displacement=None):
    apply_boundary_conditions_areas(mapdl, mech_type, percent_displacement, fixed_displacement, 'torsion',
                                    driven_constraints=lambda d: {'UX': 0, 'UY': 0, 'UZ': 0, 'ROTX': 0, 'ROTY': d, 'ROTZ': 0},
                                    fixed_constraints={'UX': 0, 'UY': 0, 'UZ': 0, 'ROTX': 0, 'ROTY': 0, 'ROTZ': 0})