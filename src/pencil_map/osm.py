import geopandas as gpd
import osmnx as ox

from pencil_map.layers import MapLayers


def safe_features_from_bbox(bbox, tags) -> gpd.GeoDataFrame:
    try:
        gdf = ox.features_from_bbox(bbox, tags)
    except Exception as exc:
        print(f"Could not fetch {tags}: {exc}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    if gdf.empty:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    return gdf


def fetch_osm_layers(bbox) -> MapLayers:
    graph = ox.graph_from_bbox(bbox, network_type="all", simplify=True)
    roads = ox.graph_to_gdfs(graph, nodes=False, edges=True)

    return MapLayers(
        roads=roads,
        waterways=safe_features_from_bbox(
            bbox, {"waterway": ["river", "stream", "canal", "drain"]}
        ),
        water=safe_features_from_bbox(bbox, {"natural": "water", "water": True}),
        forest=safe_features_from_bbox(bbox, {"landuse": "forest"}),
        wood=safe_features_from_bbox(bbox, {"natural": "wood"}),
        trees=safe_features_from_bbox(bbox, {"natural": "tree"}),
        buildings=safe_features_from_bbox(bbox, {"building": True}),
    )
