import osmnx as ox
import geopandas as gpd
import os

# Define location or shapefile
shapefile_path = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20241023_Tauberbischofsheim/QGIS/20250204/alkis/ALKIS-oE_080060_Tauberbischofsheim_shp/flurstueck.shp"  # Replace with your shapefile path
output_folder = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/POIs/"
os.makedirs(output_folder, exist_ok=True)

# Load the shapefile and get its extent (bounding box)
gdf = gpd.read_file(shapefile_path)
gdf = gdf.to_crs(epsg=4326)  # Ensure EPSG:4326 (WGS84)
extent = gdf.total_bounds
bbox = (extent[0], extent[1], extent[2], extent[3])  # (left, bottom, right, top)


# Function to retrieve and save OSM data
def retrieve_and_save_pois(osm_tags, index):
    category_name = "_".join([f"{key}-{''.join(values)}" for key, values in osm_tags.items()])
    category_filename = f"{output_folder}/POI_{index}_{category_name}.shp"

    try:
        pois = ox.features.features_from_bbox(bbox, tags=osm_tags)
    except Exception as e:
        print(f"Error retrieving POIs for {category_name}: {e}")
        return

    if pois is None or pois.empty:
        print(f"No POIs found for {category_name}. Skipping...")
        return

    # Convert polygons to their centroids
    pois['geometry'] = pois['geometry'].apply(
        lambda geom: geom.centroid if geom.geom_type in ['Polygon', 'MultiPolygon'] else geom)

    # Keep only point geometries
    pois = pois[pois.geometry.type == 'Point']

    if not pois.empty:
        pois.to_file(category_filename)
        print(f"Saved {len(pois)} POIs for {category_name} to {category_filename}.")


# Define OSM tags list
osm_tags_list = [
    {'amenity': ['kindergarten']},
    {'amenity': ['school', 'college', 'university']},
    {'highway': ['bus_stop']},
    {'amenity': ['bank', 'atm']},
    {'amenity': ['public_building', 'townhall', 'community_centre', 'conference_centre', 'courthouse', 'police', 'fire_station', 'post_office']},
    {'amenity': ['doctors', 'dentist', 'hospital', 'clinic'], 'healthcare': ['doctor', 'dentist', 'hospital', 'clinic']},
    {'amenity': ['pharmacy'], 'healthcare': ['pharmacy']},
    {'amenity': ['restaurant', 'fast_food', 'food_court', 'cafe', 'ice_cream', 'pub', 'biergarten', 'bar']},
    {'shop': ['supermarket', 'convenience'], 'amenity': ['marketplace'], 'building': ['retail']},
    {'shop': ['clothes', 'fashion', 'shoes', 'jewelry', 'computer', 'electronics', 'mobile_phone', 'cosmetics', 'beauty', 'nails', 'pet']},
    {'shop': ['swimming_pool', 'sports', 'water_sports', 'fishing', 'hunting'], 'leisure': ['stadium', 'sports_centre', 'fitness_centre', 'track', 'bowling_alley', 'miniature_golf', 'golf_course', 'pitch', 'ice_rink']},
    {'tourism': ['museum', 'gallery', 'artwork'], 'amenity': ['theatre', 'library', 'public_bookcase', 'planetarium', 'arts_centre', 'studio']},
    {'landuse': ['allotments', 'vineyard', 'forest'], 'leisure': ['park', 'nature_reserve'], 'natural': ['wood']}
]

# Process each category
for index, tags in enumerate(osm_tags_list):
    retrieve_and_save_pois(tags, index)

print("POI retrieval complete. Check the 'POIs' folder for shapefiles.")
