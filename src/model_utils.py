import pandas as pd
import logging
import numpy as np

def get_beam_model_new(mapdl, config_csv_file, element_type="BEAM188", ndiv=100, num_cross_elements=5, scale=1000.0, cross_scale=0.6, warp=False, mech_type="PET"):
    """
    Loads beam model data from a CSV file and generates the corresponding geometry in MAPDL.

    Parameters:
    - mapdl: An instance of the MAPDL class.
    - config_csv_file (str): Path to the CSV file containing the beam configuration.
    - element_type (str): Type of element to use in the simulation. Default is "BEAM188".
    - ndiv (int): Number of divisions for meshing. Default is 100.
    - num_cross_elements (int): Number of cross-sectional elements in the mesh. Default is 5.
    - scale (float): Scale factor for geometry. Default is 1000.0.
    - cross_scale (float): Cross-sectional scale factor. Default is 0.6.
    - warp (bool): Enable warping of the geometry. Default is False.
    - mech_type (str): Type of mechanism to analyze. Default is "PET".

    Returns:
    None
    """
    df_config = pd.read_csv(config_csv_file)
    df_config[['x1', 'y1', 'z1', 'x2', 'y2', 'z2']] *= scale
    df_config[['width', 'height']] *= cross_scale

    width_values = df_config['width'].unique()
    height_values = df_config['height'].unique()

    cross_section_types = {f"{i+1}": {'width': width_values[i], 'height': height_values[i]} for i in range(len(width_values))}

    for i, (key, value) in enumerate(cross_section_types.items()):
        mapdl.sectype(i+1, "BEAM", "RECT")
        mapdl.secdata(value['width'], value['height'], num_cross_elements, num_cross_elements)

    mapdl.et(1, element_type, 1, 0, 3) if warp else mapdl.et(1, element_type, 0, 0, 3)

    load_csv(mapdl, df_config)

    mapdl.lsel('ALL')
    mapdl.latt(mat=1, type_=1, secnum=1)
    mapdl.lesize('ALL', ndiv=ndiv)
    mapdl.lmesh('ALL')

    mapdl.nsel('ALL')
    mapdl.nummrg('NODE')
    mapdl.nummrg('KP')
    mapdl.endrelease()

    xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd = find_bounds(mapdl)
    # import pdb; pdb.set_trace()
    if mech_type == "KRESLING":
        process_kresling(mapdl, ymin, ymax)
    elif mech_type in ["PET", "SCISSOR"]:
        process_pet_scissor(mapdl, mech_type, ymin, ymax, zmax, zmin)

def process_kresling(mapdl, ymin, ymax):
    # select all lines at each end ymin and ymax 
    left_line_ids = mapdl.lsel(type_='S', item='LOC', comp='Y', vmin=ymin)
    # print(left_line_ids)
    left_end = mapdl.al(*left_line_ids)
    mapdl.vext(left_end, dy=-3.0)
    
    right_line_ids = mapdl.lsel(type_='S', item='LOC', comp='Y', vmin=ymax)
    # print(right_line_ids)
    right_end = mapdl.al(*right_line_ids)
    mapdl.vext(right_end, dy=3.0)
    
    # mesh the blocks
    mapdl.vsel('ALL')
    mapdl.et(2, 'SOLID187')
    mapdl.vatt(mat=1, type_=2)
    mapdl.vmesh('ALL')
    
    mapdl.nsel('ALL')
    mapdl.nummrg('NODE')

def process_pet_scissor(mapdl, mech_type, ymin, ymax, zmax, zmin):
    # Add solid block to the end of the models and connet to like bodies 
    min_y_points, max_y_points = find_endpoints(mapdl, mech_type)
    create_blocks_from_points(mapdl, min_y_points, zmax, zmin)
    create_blocks_from_points(mapdl, max_y_points, zmax, zmin)

    # mesh the blocks
    mapdl.vsel('ALL')
    mapdl.et(2, 'SOLID185')
    mapdl.vatt(mat=1, type_=2)
    mapdl.vmesh('ALL')
    
    mapdl.nsel('ALL')
    mapdl.nummrg('NODE')
    
def load_csv(mapdl, df):
    """
    Loads the geometry from a CSV file into MAPDL.

    Parameters:
    - mapdl: An instance of the MAPDL class.
    - df (DataFrame): DataFrame containing the configuration data.

    Returns:
    None
    """
    df['k1'] = (df.index * 2 + 1).astype(str)
    df['k2'] = (df.index * 2 + 2).astype(str)

    kp1_commands = 'K,' + df['k1'] + ',' + df['x1'].astype(str) + ',' + df['y1'].astype(str) + ',' + df['z1'].astype(str)
    kp2_commands = 'K,' + df['k2'] + ',' + df['x2'].astype(str) + ',' + df['y2'].astype(str) + ',' + df['z2'].astype(str)
    line_commands = 'L,' + df['k1'] + ',' + df['k2']

    all_commands = pd.concat([kp1_commands, kp2_commands, line_commands]).reset_index(drop=True)
    command_string = '\n'.join(all_commands)
    mapdl.input_strings(command_string)

def create_blocks_from_points(mapdl, points, zmax, zmin):
    """
    Creates solid blocks from specified points in MAPDL.

    Parameters:
    - mapdl: An instance of the MAPDL class.
    - points (list): List of points to create blocks from.
    - zmax (float): Maximum z-coordinate.
    - zmin (float): Minimum z-coordinate.

    Returns:
    None
    """
    sorted_points = sorted(points, key=lambda point: point[0])

    for i in range(len(sorted_points) - 1):
        x1, y1, z1 = sorted_points[i]
        x2, y2, _ = sorted_points[i + 1]
        if i == 0:
            height = abs(y2 - y1)
            if height == 0:
                height = 3.0
            
        width = x2 - x1
        depth = zmax - zmin 
        
        if depth == 0:
            depth = 3.0 
            direction = float((-1.0)**(y1 < 0))

            v1 = mapdl.blc4(x1, min(y1, y2), width, direction * height, depth)
            v2 = mapdl.blc4(x1, min(y1, y2), width, direction * height, -depth)
            # mapdl.vglue(v1, v2)
            return
        

        mapdl.blc4(x1, min(y1, y2), width, height, depth)

def find_endpoints(mapdl, mech_type):
    """
    Finds the endpoints of the keypoints in the given MAPDL object based on mechanism type.

    Parameters:
    - mapdl: An instance of MAPDL class.
    - mech_type (str): Type of mechanism to analyze.

    Returns:
    - min_y_points (list): List of minimum y-coordinate points.
    - max_y_points (list): List of maximum y-coordinate points.
    """
    nodes_coords = np.array(mapdl.geometry.get_keypoints().points)
    sorted_nodes = nodes_coords[np.argsort(nodes_coords[:, 1])]

    min_y_points = []
    max_y_points = []

    if mech_type == "PET":
        select_unique_points(sorted_nodes, min_y_points, max_y_points, 5, 3)
    elif mech_type == "SCISSOR":
        select_unique_points(sorted_nodes, min_y_points, max_y_points, 2, 2)

    return min_y_points, max_y_points

def select_unique_points(sorted_nodes, min_y_points, max_y_points, min_y_limit, max_y_limit):
    """
    Selects unique points based on y-coordinate values.

    Parameters:
    - sorted_nodes (ndarray): Array of sorted node coordinates.
    - min_y_points (list): List to store minimum y-coordinate points.
    - max_y_points (list): List to store maximum y-coordinate points.
    - min_y_limit (int): Maximum number of unique minimum y-coordinate points to select.
    - max_y_limit (int): Maximum number of unique maximum y-coordinate points to select.

    Returns:
    None
    """
    for point in sorted_nodes:
        if len(min_y_points) < min_y_limit:
            if not min_y_points or np.min([np.linalg.norm(point - p) for p in min_y_points]) > 1e-6:
                min_y_points.append(point)
        else:
            break

    for point in sorted_nodes[::-1]:
        if len(max_y_points) < max_y_limit:
            if not max_y_points or np.min([np.linalg.norm(point - p) for p in max_y_points]) > 1e-6:
                max_y_points.append(point)
        else:
            break

def find_bounds(mapdl):
    """
    Finds the bounds of the keypoints in the given MAPDL object.

    Parameters:
    - mapdl: An instance of MAPDL object.

    Returns:
    - xmin: The minimum x-coordinate of the keypoints.
    - xmax: The maximum x-coordinate of the keypoints.
    - ymin: The minimum y-coordinate of the keypoints.
    - ymax: The maximum y-coordinate of the keypoints.
    - zmin: The minimum z-coordinate of the keypoints.
    - zmax: The maximum z-coordinate of the keypoints.
    """
    logging.info("find_bounds")

    nodes_coords = mapdl.geometry.get_keypoints().points

    logging.info(f"nodes_coords: {nodes_coords}")
    logging.info(f"nodes_coords.shape: {nodes_coords.shape}")

    xmin = nodes_coords[:, 0].min()
    xmax = nodes_coords[:, 0].max()
    ymin = nodes_coords[:, 1].min()
    # ymin_2nd = nodes_coords[nodes_coords[:, 1] != ymin][:, 1].min() if len(nodes_coords[nodes_coords[:, 1] != ymin]) > 0 else ymin
    # ymax = nodes_coords[:, 1].max()
    # ymax_2nd = nodes_coords[nodes_coords[:, 1] != ymax][:, 1].max() if len(nodes_coords[nodes_coords[:, 1] != ymax]) > 0 else ymax
    if len(nodes_coords[nodes_coords[:, 1] != ymin]) > 0:
        ymin_2nd = nodes_coords[nodes_coords[:, 1] != ymin][:,1].min()
    else:
        ymin_2nd = ymin
    ymax = nodes_coords[:, 1].max()
    if len(nodes_coords[nodes_coords[:, 1] != ymax]) > 0:
        ymax_2nd = nodes_coords[nodes_coords[:, 1] != ymax][:,1].max()
    else:
        ymax_2nd = ymax
    zmin = nodes_coords[:, 2].min()
    zmax = nodes_coords[:, 2].max()

    logging.info(f"X Bounds: {xmin}, {xmax}")
    logging.info(f"Y Bounds: {ymin}, {ymax}")
    logging.info(f"Y Bounds 2nd: {ymin_2nd}, {ymax_2nd}")
    logging.info(f"Z Bounds: {zmin}, {zmax}")

    return xmin, xmax, ymin, ymax, zmin, zmax, ymin_2nd, ymax_2nd