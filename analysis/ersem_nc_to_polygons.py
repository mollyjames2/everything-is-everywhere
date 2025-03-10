# ERSEM NetCDF to Polygon Aggregation Script
#
# This script extracts and processes data from an ERSEM model output NetCDF (.nc) file and maps it to a given spatial grid (.shp file).
# It extracts phytoplankton carbon variables (P1_c, P2_c, P3_c, and P4_c) at the top siglay layer, averages them over a user-defined time range,
# sums them together, and assigns the values to polygons in a shapefile.
#
# Required Input Files:
# 1. **NetCDF File (e.g., "ersem_output.nc")**
#    - Must be generated from FVCOM-ERSEM.
#    - Contains:
#      - `time` dimension for time steps.
#      - `siglay` dimension for vertical layers.
#      - `node` dimension for spatial points.
#      - `lon(node)`, `lat(node)`: Longitude and latitude coordinates.
#      - `P1_c(time, siglay, node)`: Diatoms carbon (mg C/m³).
#      - `P2_c(time, siglay, node)`: Nanophytoplankton carbon (mg C/m³).
#      - `P3_c(time, siglay, node)`: Picophytoplankton carbon (mg C/m³).
#      - `P4_n(time, siglay, node)`: Microphytoplankton nitrogen (converted to mg C/m³).
#
# 2. **Shapefile (e.g., "grid.shp")**
#    - Contains the spatial polygons to which ERSEM data will be mapped.
#    - Used to determine which polygon each ERSEM data point falls within.
#
# Output:
# - A CSV file (e.g., "output.csv") containing:
#   - `Polygon_ID`: Unique ID of each polygon.
#   - `Average_P`: Averaged summed phytoplankton carbon value (mg C/m³) within each polygon.
#
# Source Models:
# - **FVCOM-ERSEM:** This NetCDF file can be generated using FVCOM coupled with ERSEM, available at:
#   - FVCOM Sediment Model: https://github.com/pmlmodelling/fvcom_sed
#   - ERSEM Ecosystem Model: https://github.com/pmlmodelling/ersem

import netCDF4 as nc
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

# Function to extract and average P1_c, P2_c, P3_c, and P4_c over the given time range
def extract_and_average_ersem(nc_file, start_time, end_time):
    dataset = nc.Dataset(nc_file)
    
    # Extract time variable and convert to datetime
    time_var = dataset.variables['time'][:]
    time_units = dataset.variables['time'].units
    time_dates = nc.num2date(time_var, units=time_units)
    
    # Find indices within the given time range
    time_indices = np.where((time_dates >= start_time) & (time_dates <= end_time))[0]
    
    if len(time_indices) == 0:
        raise ValueError("No data found within the specified time range.")
    
    # Extract spatial coordinates
    lon = dataset.variables['lon'][:]
    lat = dataset.variables['lat'][:]
    
    # Extract only the top siglay layer (index 0) for the P variables
    P1_c = dataset.variables['P1_c'][time_indices, 0, :]
    P2_c = dataset.variables['P2_c'][time_indices, 0, :]
    P3_c = dataset.variables['P3_c'][time_indices, 0, :]
    P4_c = dataset.variables['P4_n'][time_indices, 0, :]
    
    # Replace missing values with NaN
    fill_value = dataset.variables['P1_c']._FillValue
    P1_c[P1_c == fill_value] = np.nan
    P2_c[P2_c == fill_value] = np.nan
    P3_c[P3_c == fill_value] = np.nan
    P4_c[P4_c == fill_value] = np.nan
    
    # Compute mean over time for each variable
    P1_avg = np.nanmean(P1_c, axis=0)
    P2_avg = np.nanmean(P2_c, axis=0)
    P3_avg = np.nanmean(P3_c, axis=0)
    P4_avg = np.nanmean(P4_c, axis=0)
    
    # Sum all P variables
    total_P = P1_avg + P2_avg + P3_avg + P4_avg
    
    # Create DataFrame with spatial coordinates and total P value
    data = pd.DataFrame({'lon': lon, 'lat': lat, 'Total_P': total_P})
    return data

# Function to map ERSEM data to polygons
def map_to_polygons(ersem_data, shapefile):
    grid = gpd.read_file(shapefile)
    
    # Convert ERSEM data to GeoDataFrame
    points = gpd.GeoDataFrame(ersem_data, geometry=gpd.points_from_xy(ersem_data.lon, ersem_data.lat), crs=grid.crs)
    
    # Perform spatial join
    joined = gpd.sjoin(points, grid, how='left', predicate='within')
    
    # Group by polygon ID and compute mean value
    polygon_data = joined.groupby(joined.index_right)['Total_P'].mean().reset_index()
    polygon_data.rename(columns={'index_right': 'Polygon_ID', 'Total_P': 'Average_P'}, inplace=True)
    
    return polygon_data

# Main function
def process_ersem_to_polygons(nc_file, shapefile, start_time, end_time, output_csv):
    ersem_data = extract_and_average_ersem(nc_file, start_time, end_time)
    polygon_data = map_to_polygons(ersem_data, shapefile)
    polygon_data.to_csv(output_csv, index=False)
    print(f"CSV saved: {output_csv}")

# Example usage
# from datetime import datetime
# process_ersem_to_polygons("ersem_output.nc", "grid.shp", datetime(2024, 1, 1), datetime(2024, 1, 10), "output.csv")

