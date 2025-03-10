# Connectivity Analysis Script
# This script processes connectivity data, builds network graphs, detects communities, calculates key metrics, and computes self-recruitment.

# Required Input Files:
# 1. **settlement_7d.csv, settlement_14d.csv, settlement_21d.csv, settlement_28d.csv**
#    - Format: CSV
#    - Contains connectivity data for different pelagic larval durations (PLD).
#    - Expected columns:
#      - Column 4: Release polygon ID
#      - Column 11: Settlement polygon ID
#    - Particles that settle outside the domain are labeled as "outside grid domain".
#
# 2. **release_locs.csv**
#    - Format: CSV
#    - Contains spatial information for release locations.
#    - Expected columns:
#      - "LAT" (Latitude)
#      - "LON" (Longitude)
#
# 3. **structures.shp** (Optional, for analyzing connectivity between structures only)
#    - Format: Shapefile
#    - Contains the locations of offshore structures.
#    - Must include geometry (points) with latitude and longitude attributes.
#
# Output Files:
# - Processed connectivity matrices and network statistics saved under `./environments/`
# - Visualization of the network graph saved as `network_map.png`
# - A CSV file (`community_assignments.csv`) mapping each polygon to its detected community
# - A CSV file (`self_recruitment.csv`) showing self-recruitment values for each polygon

# Set the working directory (Ensure you update this to your local path)
# setwd("/path/to/working/directory")

# Load required libraries
library(dplyr)
library(reshape2)
library(igraph)
library(rworldxtra)
library(raster)
library(maps)
library(readr)
library(data.table)
library(rgdal)
library(rgeos)

# Load and process connectivity data for different PLD durations
process_connectivity_data <- function(file_path) {
  # Load connectivity data from CSV
  connectivity <- read_csv(file_path)
  
  # Rename columns to match expected structure
  colnames(connectivity)[4]  <- "Release_poly"  
  colnames(connectivity)[11]  <- "Settlement_poly"  
  
  # Count particles that settle outside the domain
  out_percentage <- (sum(connectivity$Settlement_poly == "outside grid domain") / nrow(connectivity)) * 100
  cat('Percentage of particles outside of domain:', out_percentage, '%\n')
  
  # Remove rows where particles settled outside the domain
  connectivity <- subset(connectivity, connectivity$Settlement_poly != "outside grid domain")
  
  # Format settlement polygon IDs
  connectivity$Settlement_poly <- as.double(connectivity$Settlement_poly)
  
  # Summarize the connectivity matrix
  myFreqs <- connectivity %>%  
    group_by(Release_poly, Settlement_poly) %>% 
    summarise(Count = n(), .groups = 'drop')
  
  # Generate all possible polygon combinations
  poly_ids <- unique(c(unique(connectivity$Release_poly), unique(connectivity$Settlement_poly)))
  all_pairs <- expand.grid(Release_poly = poly_ids, Settlement_poly = poly_ids)
  
  # Merge observed connectivity matrix with all possible combinations
  myFreqs <- merge(all_pairs, myFreqs, all.x = TRUE)
  myFreqs[is.na(myFreqs)] <- 0
  
  # Convert to adjacency matrix
  s.dat <- acast(myFreqs, Release_poly ~ Settlement_poly, value.var = "Count")
  
  return(list(matrix = s.dat, freqs = myFreqs))
}

# Process connectivity data for different PLD values
connectivity_7d <- process_connectivity_data("settlement_7d.csv")
connectivity_14d <- process_connectivity_data("settlement_14d.csv")
connectivity_21d <- process_connectivity_data("settlement_21d.csv")
connectivity_28d <- process_connectivity_data("settlement_28d.csv")

# Load release locations for mapping
centroids <- read_csv("release_locs.csv")

# Optionally filter for connectivity between structures only
use_structures <- FALSE  # Set to TRUE to analyze connectivity only between structures
if (use_structures) {
  structures <- readOGR("structures.shp")
  centroids_sf <- st_as_sf(centroids, coords = c("LON", "LAT"), crs = st_crs(structures))
  centroids <- centroids[st_intersects(centroids_sf, structures, sparse = FALSE), ]
}

# Combine graph data into one unified network
df_edges <- rbind(as_data_frame(connectivity_7d$freqs), as_data_frame(connectivity_14d$freqs), 
                  as_data_frame(connectivity_21d$freqs), as_data_frame(connectivity_28d$freqs))

df_edges <- data.table(df_edges)
df_edges <- df_edges[, lapply(.SD, sum), by = list(Release_poly, Settlement_poly)]
df_edges <- as.data.frame(df_edges)

# Create final graph
combined_graph <- graph_from_data_frame(df_edges, directed=TRUE)

# Community detection using Louvain method
ceb <- cluster_fast_greedy(as.undirected(combined_graph), weights=NULL)

# Compute self-recruitment (where release and settlement polygons are the same)
self_recruitment <- df_edges %>% filter(Release_poly == Settlement_poly) %>% 
  select(Release_poly, Count) %>% 
  rename(Self_Recruitment = Count)

# Save self-recruitment results
write.csv(self_recruitment, "./environments/self_recruitment.csv", row.names = FALSE)

# Save community assignments
community_assignments <- data.frame(Node=V(combined_graph)$name, Community=membership(ceb))
write.csv(community_assignments, "./environments/community_assignments.csv", row.names = FALSE)

# Export connectivity edges
write.csv(df_edges, "./environments/edges.csv", row.names = FALSE)

# Save the map plot
png("network_map.png", width=1200, height=800)
plot(ceb, combined_graph, vertex.size=0, vertex.label=NA, edge.arrow.size=0.5)
dev.off()

# The script processes connectivity data for different PLD durations, builds a network graph, detects communities, calculates key graph metrics, and computes self-recruitment.
