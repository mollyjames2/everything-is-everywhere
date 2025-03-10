import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.stats import zscore
from sklearn.preprocessing import MinMaxScaler

def generate_analysis_csv(in_degree_file, out_degree_file, betweenness_file, food_availability_file, self_recruitment_file, community_file, structure_shp, grid_shp, output_csv):
    """
    Generates a comprehensive CSV file containing network metrics, food availability, self-recruitment, 
    and community assignments, along with normalized and standardized z-scores.
    
    Parameters:
        in_degree_file (str): Path to the CSV file containing in-degree values.
        out_degree_file (str): Path to the CSV file containing out-degree values.
        betweenness_file (str): Path to the CSV file containing betweenness values.
        food_availability_file (str): Path to the CSV file containing food availability values.
        self_recruitment_file (str): Path to the CSV file containing self-recruitment values.
        community_file (str): Path to the CSV file containing community assignments.
        structure_shp (str): Path to the shapefile containing structure locations.
        grid_shp (str): Path to the shapefile containing grid polygons.
        output_csv (str): Path to save the output CSV file.
    """
    # Load input data
    in_degree = pd.read_csv(in_degree_file)
    out_degree = pd.read_csv(out_degree_file)
    betweenness = pd.read_csv(betweenness_file)
    food_av = pd.read_csv(food_availability_file)
    self_recruitment = pd.read_csv(self_recruitment_file)
    community = pd.read_csv(community_file)
    
    # Load structure and grid shapefiles
    structures = gpd.read_file(structure_shp)
    grid = gpd.read_file(grid_shp)
    
    # Spatial join to determine which grid cells contain structures
    grid["contains_structure"] = grid.geometry.apply(lambda x: structures.geometry.intersects(x).any())
    
    # Convert grid data to DataFrame for merging
    grid_df = grid[["geometry"]].reset_index()
    grid_df.rename(columns={"index": "Cell ID"}, inplace=True)
    
    # Merge all data into a single DataFrame
    df = grid_df.merge(in_degree, left_on="Cell ID", right_on="Node", how="left")
    df = df.merge(out_degree, on="Node", how="left")
    df = df.merge(betweenness, on="Node", how="left")
    df = df.merge(food_av, on="Node", how='left')
    df = df.merge(self_recruitment, on="Node", how='left')
    df = df.merge(community, on="Node", how='left')
    df = df.merge(grid[["Cell ID", "contains_structure"]], on="Cell ID", how='left')
    
    # Rename columns
    df.rename(columns={
        "Node": "Cell ID",
        "Out_Degree": "out",
        "In_Degree": "in",
        "Betweenness": "node_betw",
        "Food_Availability": "food_av",
        "Self_Recruitment": "sr",
        "Community": "community"
    }, inplace=True)
    
    # Normalize selected columns
    normalize_cols = ["out", "in", "node_betw", "food_av"]
    scaler = MinMaxScaler()
    df[[f"norm_{col}" for col in normalize_cols]] = scaler.fit_transform(df[normalize_cols])
    
    # Compute Z-scores
    df[[f"z_{col}" for col in normalize_cols]] = df[[f"norm_{col}" for col in normalize_cols]].apply(zscore, nan_policy='omit')
    
    # Sum of Z-scores
    df["z_sum"] = df[[f"z_{col}" for col in normalize_cols]].sum(axis=1)
    
    # Standardize Z-sum
    df["standard_z_sum"] = 2 * (df["z_sum"] - df["z_sum"].min()) / (df["z_sum"].max() - df["z_sum"].min()) - 1
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"Analysis CSV saved: {output_csv}")

# Example usage:
# generate_analysis_csv(
#     "./outputs/in_degree.csv", "./outputs/out_degree.csv", "./outputs/node_betweenness.csv", 
#     "./outputs/food_availability.csv", "./outputs/self_recruitment.csv", "./outputs/community_assignments.csv", 
#     "./outputs/structures.shp", "./outputs/grid.shp", "./outputs/analysis_output.csv")

