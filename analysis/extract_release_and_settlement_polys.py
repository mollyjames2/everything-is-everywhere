# NC to CSV Conversion Script
#
# This script processes a NetCDF (.nc) file containing particle tracking data and a shapefile (.shp) representing a spatial grid.
# It assigns each particle to a polygon based on its initial and final positions and outputs a CSV file containing:
# - particleID: Unique identifier for each particle (starting from 1)
# - Release_poly: The polygon where the particle was released
# - Settlement_poly: The polygon where the particle settled (or 'outside grid domain' if not in any polygon)
#
# Required Input Files:
# 1. **NetCDF File (e.g., "particles.nc")**
#    - Must contain:
#      - `particles` dimension (Number of tracked particles)
#      - `x(time, particles)`: X coordinates of particles over time
#      - `y(time, particles)`: Y coordinates of particles over time
#
# 2. **Shapefile (e.g., "grid.shp")**
#    - Must represent the spatial grid as polygons
#    - Used to determine the release and settlement polygons
#
# Output:
# - A CSV file (e.g., "output.csv") containing the particle assignments to polygons

import netCDF4 as nc
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Function to extract first and last positions from NC file
def extract_particle_positions(nc_file):
    dataset = nc.Dataset(nc_file)
    
    # Get the number of particles from dimensions
    num_particles = dataset.dimensions['particles'].size
    
    # Generate particle IDs starting from 1
    particle_ids = list(range(1, num_particles + 1))
    
    # Extract relevant variables
    x_positions = dataset.variables['x'][:]
    y_positions = dataset.variables['y'][:]
    
    # First and last positions
    first_positions = [Point(x_positions[0, i], y_positions[0, i]) for i in range(num_particles)]
    last_positions = [Point(x_positions[-1, i], y_positions[-1, i]) for i in range(num_particles)]
    
    return particle_ids, first_positions, last_positions

# Function to assign particles to polygons
def assign_polygons(particle_ids, first_positions, last_positions, shapefile):
    grid = gpd.read_file(shapefile)
    
    # Convert to GeoDataFrame
    first_df = gpd.GeoDataFrame({'particleID': particle_ids, 'geometry': first_positions}, crs=grid.crs)
    last_df = gpd.GeoDataFrame({'particleID': particle_ids, 'geometry': last_positions}, crs=grid.crs)
    
    # Spatial join to get polygon IDs
    first_joined = gpd.sjoin(first_df, grid, how='left', predicate='within')
    last_joined = gpd.sjoin(last_df, grid, how='left', predicate='within')
    
    # Assign 'outside grid domain' to particles that do not settle within a polygon
    last_joined['Settlement_poly'] = last_joined.index_right.fillna('outside grid domain')
    
    # Merge results
    results = pd.DataFrame({
        'particleID': particle_ids,
        'Release_poly': first_joined['Release_poly'],
        'Settlement_poly': last_joined['Settlement_poly']
    })
    
    return results

# Main function
def process_nc_to_csv(nc_file, shapefile, output_csv):
    particle_ids, first_positions, last_positions = extract_particle_positions(nc_file)
    results = assign_polygons(particle_ids, first_positions, last_positions, shapefile)
    results.to_csv(output_csv, index=False)
    print(f"CSV saved: {output_csv}")

# Example usage
# process_nc_to_csv("particles.nc", "grid.shp", "output.csv")

