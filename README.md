# HERDS and PETs Ansys Analysis

## Project Overview

This project involves the simulation and analysis of Hierarchical Extending and Reorienting Deployable Structures (HERDS), Kresling Mechanism, and Pop-Up Extending Truss (PET) structures using ANSYS Mechanical APDL. The simulations include various tests and configurations to evaluate the structural performance under different conditions.

## Project Structure

The project is organized into the following directories:

- `data/`: Contains the input data, results, and plots for the simulations.
  - `models/`: Includes the model data for HERDS and PETs.
    - `herds/`: Model data for HERDS structures.
    - `pets/`: Model data for PET structures.
    - `kresling/`: Model data for Kresling structures.
    - `short_scissor/`: Model data for short member scissor structures.
    - `long_scissor/`: Model data for long member scissor structures.
  - `results/`: Simulation results. 
  - `paper_results/`: The official simulations results used in the paper. 
  - `plots/`: Generated plots from the simulation results.
- `scripts/`: Scripts to generate all data and generate figures.
  - `generate_figures`: Scripts to generate all figures.
  - `generate_results`: Scripts to genertate all results.
- `src/`: Source code for the project.
  - `run_ansys_simulation.py`: The main simulation loop.
  - `ansys_utils.py`: Utility functions for running ANSYS simulations.
  - `model_utils.py`: Functions for generating the beam models.
  - `boundary_conditions.py`: Functions for applying boundary conditions.
  - `parser_utils.py`: Argument parser utilities.
  - `logging_utils.py`: Logging utilities.

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/mfogelson/herds_pets_ansys_analysis.git
    cd herds_pets_ansys_analysis
    ```

2. **Set up the environment:**
    Ensure you have the necessary dependencies installed. You may want to create a virtual environment:

    ```sh
   conda create --name herds_pets_env python=3.10
   conda activate herds_pets_env
   pip install -r requirements.txt
    ```

3. **Ensure ANSYS is installed and configured:**
    The scripts require ANSYS Mechanical APDL to be installed and properly configured on your system.

## Usage

### Running Simulations

1. **Prepare the input data:**
    Ensure the model configuration CSV files are placed in the appropriate directory under `data/models/`.

2. **Run a simulation:**
    Use the provided scripts to run simulations with various configurations. For example, to run a simulation for a PET structure with a specific configuration, use:

    ```sh
    python src/run_ansys_simulation.py <filesname> <filepath> <boundary_condition>
    ```

    You can specify additional parameters as needed.

    ```sh
    python src/run_ansys_simulation.py "l1_17.16_l2_3.7_l3_30.64_alpha_0.6_cross_3.0x3.0_n_cells_3.csv" "data/models/pets/deployment_test" "cant_x" --scale 5 --mech_type PET --cross_scale 0.6
    ```
    **NOTE:** The flags and defaults can be found in `src/parser_utils.py` 

### Generating Figures

1. **Generate figures from simulation results:**
    Use the scripts in the `scripts/` directory to generate figures from the simulation results. For example, to generate a plot for the deployment test:

    ```sh
    python scripts/generate_figures/figure3a_deployment_test_script.py
    ```

    **NOTE:** The path is currenly configured to `data/paper_results` this must be updated in the script to plot new results from `data/results`

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any questions or issues, please contact [mfogelson@cmu.edu](mailto:mfogelson@cmu.edu).

## Citation

```
@article{thomas2024nonplanar,
  title={Non-Planar Hierarchical Composition of Extending Metamaterials for Deployable Load-Bearing Structures},
  author={Thomas, Sawyer and Fogelson, Mitchell B. and Manchester, Zachary and Lipton, Jeffrey I.},
  year={2024},
  url={https://www.github.com/mfogelson/herds_pets_ansys_analysis}  
}
```