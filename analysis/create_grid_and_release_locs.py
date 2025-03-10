import geopandas as gpd
import numpy as np
from shapely.geometry import box
import pandas as pd

def generate_grid(min_lat, max_lat, min_lon, max_lon, cell_size_km, gebco_mask_shp):
    """
    Generates a multi-polygon grid over a given area and removes land areas using a GEBCO land mask shapefile.
    
    Parameters:
        min_lat (float): Minimum latitude
        max_lat (float): Maximum latitude
        min_lon (float): Minimum longitude
        max_lon (float): Maximum longitude
        cell_size_km (float): Cell size in kilometers (e.g., 30 for a 30x30 km grid)
        gebco_mask_shp (str): Path to the GEBCO land mask shapefile (.shp file)
    
    Returns:
        gpd.GeoDataFrame: Grid with only ocean polygons, clipped to match coastline
    """
    # Convert cell size from km to degrees (~1 degree = 111 km at the equator)
    cell_size_deg = cell_size_km / 111.0
    
    # Generate grid cells
    grid_cells = []
    lat_steps = np.arange(min_lat, max_lat, cell_size_deg)
    lon_steps = np.arange(min_lon, max_lon, cell_size_deg)
    
    for lat in lat_steps:
        for lon in lon_steps:
            grid_cells.append(box(lon, lat, lon + cell_size_deg, lat + cell_size_deg))
    
    # Create GeoDataFrame
    grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
    
    # Load GEBCO land mask as a shapefile
    land_mask = gpd.read_file(gebco_mask_shp)
    
    # Remove grid cells completely on land
    grid = grid[~grid.geometry.within(land_mask.unary_union)]
    
    # Clip grid cells that partially intersect land
    grid["geometry"] = grid.geometry.apply(lambda g: g.difference(land_mask.unary_union))
    
    # Remove empty geometries
    grid = grid[~grid.geometry.is_empty]
    
    return grid

def save_grid_as_shapefile(grid, output_shapefile):
    """Saves the generated grid as a shapefile."""
    grid.to_file(output_shapefile)
    print(f"Shapefile saved: {output_shapefile}")

def save_centroids_as_csv(grid, output_csv):
    """Saves the centroid coordinates of each polygon in the grid as a CSV file."""
    grid["centroid_lat"] = grid.geometry.centroid.y
    grid["centroid_lon"] = grid.geometry.centroid.x
    centroids_df = grid[["centroid_lat", "centroid_lon"]]
    centroids_df.to_csv(output_csv, index=False)
    print(f"CSV saved: {output_csv}")

# Example Usage:
# ocean_grid = generate_grid(min_lat=50, max_lat=60, min_lon=-10, max_lon=5, cell_size_km=30, gebco_mask_shp="gebco_mask.shp")
# save_grid_as_shapefile(ocean_grid, "grid.shp")
# save_centroids_as_csv(ocean_grid, "release_locs.csv")

