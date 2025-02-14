import os
import glob
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin


def shapefiles_to_raster(input_folder, output_raster, resolution=1):
    shapefiles = glob.glob(os.path.join(input_folder, "*.shp"))

    if not shapefiles:
        print("No shapefiles found in the input folder.")
        return

    # Read first shapefile to get CRS
    sample_gdf = gpd.read_file(shapefiles[0])

    # Initialize metric_crs variable
    metric_crs = sample_gdf.crs  # Default to the original CRS

    # If in degrees, reproject to a metric CRS (e.g., UTM)
    if sample_gdf.crs.to_string().startswith("EPSG:4326"):
        print("Reprojecting shapefiles to a metric CRS...")
        metric_crs = sample_gdf.estimate_utm_crs()
        shapefiles_gdfs = [gpd.read_file(shp).to_crs(metric_crs) for shp in shapefiles]
    else:
        shapefiles_gdfs = [gpd.read_file(shp) for shp in shapefiles]

    # Get total bounds in the projected CRS
    all_bounds = [gdf.total_bounds for gdf in shapefiles_gdfs]
    minx = min(b[0] for b in all_bounds)
    miny = min(b[1] for b in all_bounds)
    maxx = max(b[2] for b in all_bounds)
    maxy = max(b[3] for b in all_bounds)

    # Compute raster dimensions safely
    width = max(1, int((maxx - minx) / resolution))
    height = max(1, int((maxy - miny) / resolution))

    print(f"Projected Bounds: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")
    print(f"Raster size: width={width}, height={height}")

    # Define transform
    transform = from_origin(minx, maxy, resolution, resolution)

    # Initialize empty raster
    final_raster = np.zeros((height, width), dtype=np.uint8)

    for gdf in shapefiles_gdfs:
        shapes = [(geom, 1) for geom in gdf.geometry]

        # Rasterize current shapefile
        raster = rasterize(shapes, out_shape=(height, width), transform=transform, fill=0, dtype='uint8')

        # Add to final raster
        final_raster += raster

    # Define raster metadata
    out_meta = {
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": 0,
        "width": width,
        "height": height,
        "count": 1,
        "crs": metric_crs,
        "transform": transform,
    }

    # Save final raster
    with rasterio.open(output_raster, "w", **out_meta) as dst:
        dst.write(final_raster, 1)

    print(f"Final raster saved: {output_raster}")


# Example usage
input_folder = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/isochrone/"
output_raster = "C:/Users/janni/Documents/00_eagle/UrbanFormAndSociety/20250205_15mincity/isochrone/traveltime.tif"
shapefiles_to_raster(input_folder, output_raster)
