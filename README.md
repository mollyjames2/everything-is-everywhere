# everything-is-everywhere analysis
This repository contains network analysis code under the 'everything is everywhere' approach for creating a connectivity importance index for a grid, using the outputs from the ERSEM biogeochemical model and particle tracking simulations and PyLag, coupled to the FVCOM hydrodyanmic model 

## Related Models
The following models were used in this study:

- [FVCOM Model](https://github.com/pmlmodelling/fvcom_sed)
- [ERSEM Model](https://github.com/pmlmodelling/ersem)
- [PyLag Model](https://github.com/pmlmodelling/pylag)

## Analysis Code
The `analysis/` directory contains Python and R scripts for processing the outputs of FVCOM-ERSEM and FVCOM-PYLAG to generate the connectivity importance index for the grid defined in the create_grid_and release_locs.py file.

## How to Use
1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/everything-is-everywhere-analysis.git

2. Follow the setup instructions in each model’s documentation.

3. Run the analysis scripts in analysis/
  - create_grid_and_release_locs.py will generate a uniform grid of polygons over a given area and provide a cav file of release locations for the centroid of each polygon to be used with pylag
  - connectivity_analysys.R will perform a network analysis using igraph to determine the in-degree, out-degree, node_betweenness, self-recruitment and community assignment of each polygon
  - ersem_nc_to_polygons.py will determine the total surface phytoplankton biomass, averaged over time, for each polygon
  - create_grid_polygon_metrics_df.py will combine network metrics (in-degree, out-degree, betweenness), food availability, self-recruitment, and community assignments, integrating them with spatial data from a grid and structure shapefile. It normalizes and computes z-      scores for key metrics, generating a final CSV with comprehensive spatial and connectivity analysis. The script also sums and standardizes these metrics to compute a Connectivity Importance Index (CII) for each grid polygon, allowing for easy comparison of relative      importance across the study area

(inputs are provided in the form of the release_locs.csv, structures.shp and grid.shp used in this study)

## Citation
This repository supports the work undertaken in following publication:
[AUTHORS] (2025) The ‘everything is everywhere’ framework: Holistic network analysis as a marine spatial management tool. [JOURNAL] [DOI]

If you use this repository, please cite the above publication
