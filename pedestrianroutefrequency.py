import os
import osmnx as ox
import geopandas as gpd
import networkx as nx
from collections import defaultdict


def load_data(buildings_path, pois_dir):
    buildings = gpd.read_file(buildings_path).to_crs(epsg=32632)  # Convert to UTM32
    pois_files = [os.path.join(pois_dir, f) for f in os.listdir(pois_dir) if f.endswith('POI_8_shop-supermarktconvenience_amenity-marketplace_building-retail.shp')]

    # Create a dictionary where keys are categories (filenames) and values are GeoDataFrames
    pois = {os.path.basename(p).split('.')[0]: gpd.read_file(p).to_crs(epsg=32632) for p in pois_files}

    return buildings, pois


def get_street_network(place_name):
    G = ox.graph_from_place(place_name, network_type='walk')
    G = ox.project_graph(G, to_crs='epsg:32632')  # Convert to UTM32
    return G


def snap_points_to_nearest_node(G, gdf):
    gdf['nearest_node'] = gdf.geometry.apply(lambda x: ox.distance.nearest_nodes(G, x.x, x.y))
    return gdf


def find_nearest_poi_by_walking(G, building_node, category_pois):
    """
    Finds the nearest POI in a given category based on the shortest walking distance.
    """
    min_distance = float('inf')
    nearest_poi = None

    for _, poi in category_pois.iterrows():
        poi_node = poi['nearest_node']
        try:
            distance = nx.shortest_path_length(G, source=building_node, target=poi_node, weight='length')
            if distance < min_distance:
                min_distance = distance
                nearest_poi = poi
        except nx.NetworkXNoPath:
            continue  # No valid path between building and POI, ignore it

    return nearest_poi, min_distance


def compute_routes(G, buildings, pois):
    """
    Finds the nearest POI by walking distance for each category, then computes the shortest routes.
    """
    route_counts = defaultdict(int)

    for _, building in buildings.iterrows():
        building_node = building['nearest_node']

        for category, category_pois in pois.items():
            nearest_poi, _ = find_nearest_poi_by_walking(G, building_node, category_pois)
            if nearest_poi is None:
                continue  # Skip if no POI found in this category

            source, target = building_node, nearest_poi['nearest_node']
            try:
                route = nx.shortest_path(G, source, target, weight='length')
                for u, v in zip(route[:-1], route[1:]):
                    route_counts[(u, v)] += 1
                    route_counts[(v, u)] += 1  # Account for undirected nature
            except nx.NetworkXNoPath:
                continue  # Skip if no valid path exists

    return route_counts


def save_route_frequencies(G, route_counts, output_path):
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
    edges['route_freq'] = edges.apply(lambda row: route_counts.get((row.name[0], row.name[1]), 0), axis=1)
    edges.to_crs(epsg=32632).to_file(output_path)  # Ensure output is in UTM32


def main():
    buildings_path = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/other/buildings_centroids.shp"
    pois_dir = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/other/"
    output_path = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/other/road_network_with_routes.shp"
    place_name = "Tauberbischofsheim, Germany"

    # Load data
    buildings, pois = load_data(buildings_path, pois_dir)

    # Load street network
    G = get_street_network(place_name)

    # Snap buildings and POIs to the street network
    buildings = snap_points_to_nearest_node(G, buildings)
    for category in pois:
        pois[category] = snap_points_to_nearest_node(G, pois[category])

    # Compute shortest paths and route frequencies
    route_counts = compute_routes(G, buildings, pois)

    # Save results
    save_route_frequencies(G, route_counts, output_path)
    print(f'Saved output to {output_path}')


if __name__ == "__main__":
    main()
