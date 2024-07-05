# Generate Figures

These scripts contain the code to process the results from the data/results folder and generate the figures that are seen in the paper.

### Directory Structure

* scripts/generate_figures/figure3a_deployment_test_script.py
* scripts/generate_figures/figure3b_aspect_ratio_scaling_script.py
* scripts/generate_figures/figure4_extension_ratio_sweep_script.py

### Usage
Run this from the project directory:
```
python scripts/generate_figures/<generate_figure>.py
```
The plots are saved to **data/plots/<test_name>**

### Dependencies

* pandas
* matplotlib
* numpy
* concurrent.futures
* os
* re

Install the dependencies using:
```
pip install pandas matplotlib numpy
```

### Notes
* The script uses ThreadPoolExecutor for parallel processing of the CSV files to speed up the computation.
* Ensure the CSV files are named correctly and contain the necessary columns (L, Displacement, FX, FY, FZ).
* The plot is saved in SVG format for high-quality vector graphics.