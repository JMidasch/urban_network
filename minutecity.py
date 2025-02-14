import osmnx as ox
import networkx as nx
import geopandas as gpd
import os

# Define the folder where POIs and output will be saved
pois_folder = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/POIs/"
output_folder = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/isochrone/"
os.makedirs(output_folder, exist_ok=True)

# Define the bounding box (you can hardcode it or pass it from the first script)
shapefile_path = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20241023_Tauberbischofsheim/QGIS/20250204/alkis/ALKIS-oE_080060_Tauberbischofsheim_shp/flurstueck.shp"

# Load the shapefile and ensure it's in EPSG:4326
gdf = gpd.read_file(shapefile_path).to_crs(epsg=4326)

# Get the bounding box (left, bottom, right, top)
extent = gdf.total_bounds
bbox = (extent[0], extent[1], extent[2], extent[3])
print(f"Shapefile extent: {bbox}")

# Retrieve street network for walking
try:
    G = ox.graph_from_bbox(bbox, network_type="walk")
    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)
    print("Street network retrieved successfully.")
except Exception as e:
    print(f"Error retrieving street network: {e}")
    G = None

# Function to calculate 15-minute isochrones
def calculate_isochrone(g, center_node, travel_time=900*1.4):
    subgraph = nx.ego_graph(g, center_node, radius=travel_time, distance="length")
    nodes, _ = ox.graph_to_gdfs(subgraph, nodes=True, edges=True)
    return nodes.geometry.union_all().convex_hull  # Improved convex hull calculation


# Process each POI shapefile and generate isochrones
for pois_file in os.listdir(pois_folder):
    if pois_file.endswith(".shp"):
        category = pois_file.replace("_pois.shp", "")
        pois_gdf = gpd.read_file(os.path.join(pois_folder, pois_file))

        # Ensure POIs are in EPSG:4326
        if pois_gdf.crs != "EPSG:4326":
            pois_gdf = pois_gdf.to_crs(epsg=4326)

        print(f"Processing POI category: {category}")
        isochrones = []

        for idx, poi in pois_gdf.iterrows():
            try:
                if poi.geometry is None or not poi.geometry.is_valid:
                    print(f"Invalid geometry for POI {poi.get('name', 'Unnamed')}. Skipping...")
                    continue

                print(f"POI '{poi.get('name', 'Unnamed')}' at ({poi.geometry.x}, {poi.geometry.y})")

                # Get nearest street network node
                nearest_node = ox.distance.nearest_nodes(G, X=poi.geometry.x, Y=poi.geometry.y)

                if nearest_node is None:
                    print(f"Warning: No nearest node found for {poi.get('name', 'Unnamed')}. Skipping...")
                    continue

                # Compute isochrone
                iso_poly = calculate_isochrone(G, nearest_node)
                isochrones.append([poi.get('name', 'Unnamed'), iso_poly])
                print(f"Isochrone for {poi.get('name', 'Unnamed')} generated.")

            except Exception as e:
                print(f"Skipping {poi.get('name', 'Unnamed')} due to error: {e}")

        # Save results as shapefile if any isochrones were created
        if isochrones:
            gdf_isochrones = gpd.GeoDataFrame(isochrones, columns=['name', 'geometry'], crs='EPSG:4326')
            gdf_isochrones.to_file(f"{output_folder}/isochrones_{category}.shp")
            print(f"Saved {category} isochrones as shapefile.")

print("Isochrone generation complete. Check the 'isochrone' folder for shapefiles.")
