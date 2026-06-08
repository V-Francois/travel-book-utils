import osmnx as ox
import geopandas as gpd
from shapely.geometry import box


north = 47.6897
south = 47.5884
# west = 3.6729
west = 3.66
# east = 3.7799
east = 3.77

region = box(west, south, east, north)

tags = {"landuse": True, "natural": True, "waterway": True}

print("Downloading features...")
gdf = ox.features_from_polygon(region, tags=tags)

print("Downloading roads...")
roads_graph = ox.graph_from_polygon(region, network_type="drive")

roads = ox.graph_to_gdfs(roads_graph, nodes=False)

gdf.to_file("landcover.geojson", driver="GeoJSON")
roads.to_file("roads.geojson", driver="GeoJSON")

print("Done")
