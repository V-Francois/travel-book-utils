from dataclasses import dataclass, field
from typing import Any

import geopandas as gpd


def _empty_gdf(crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[], crs=crs)


@dataclass
class MapLayers:
    roads: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    waterways: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    water: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    forest: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    wood: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    trees: gpd.GeoDataFrame = field(default_factory=_empty_gdf)
    buildings: gpd.GeoDataFrame = field(default_factory=_empty_gdf)


@dataclass(frozen=True)
class PreparedMap:
    route: gpd.GeoDataFrame
    places: gpd.GeoDataFrame
    major_roads: gpd.GeoDataFrame
    minor_roads: gpd.GeoDataFrame
    waterways: gpd.GeoDataFrame
    water: gpd.GeoDataFrame
    forest: gpd.GeoDataFrame
    wood: gpd.GeoDataFrame
    trees: gpd.GeoDataFrame
    buildings: gpd.GeoDataFrame
    target_crs: Any
    extent: tuple[float, float, float, float]


def bbox_from_route(route_gdf: gpd.GeoDataFrame, buffer_meters: int):
    if route_gdf.empty:
        return None

    buffered = route_gdf.to_crs(route_gdf.estimate_utm_crs()).buffer(buffer_meters)
    minx, miny, maxx, maxy = buffered.to_crs("EPSG:4326").total_bounds
    return (minx, miny, maxx, maxy)


def keep_geom_types(gdf: gpd.GeoDataFrame, geom_types: list[str]) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.isin(geom_types)].copy()


def is_major_road(highway) -> bool:
    values = highway if isinstance(highway, list) else [highway]
    major_types = {
        "motorway",
        "trunk",
        "primary",
        "secondary",
        "tertiary",
        "primary_link",
        "secondary_link",
        "tertiary_link",
    }
    return any(value in major_types for value in values)


def _project(gdf: gpd.GeoDataFrame, target_crs) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gpd.GeoDataFrame(gdf.copy(), geometry="geometry", crs=target_crs)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf.to_crs(target_crs)


def prepare_layers(
    route: gpd.GeoDataFrame,
    places: gpd.GeoDataFrame,
    layers: MapLayers,
    buffer_meters: int,
) -> PreparedMap:
    if route.empty:
        raise ValueError("Route GeoDataFrame must contain at least one geometry")

    route = keep_geom_types(route, ["LineString", "MultiLineString"])
    if route.empty:
        raise ValueError("Route must contain LineString or MultiLineString geometry")

    target_crs = route.estimate_utm_crs()
    route = _project(route, target_crs)
    places = _project(places, target_crs)

    roads = layers.roads.copy()
    if not roads.empty:
        roads = roads[["geometry", "highway"]].copy()
        roads = roads.set_crs("EPSG:4326", allow_override=True)
    roads = _project(roads, target_crs)

    roads["is_major"] = (
        roads["highway"].apply(is_major_road) if "highway" in roads else False
    )
    major_roads = roads[roads["is_major"]].copy() if not roads.empty else roads.copy()
    minor_roads = roads[~roads["is_major"]].copy() if not roads.empty else roads.copy()

    waterways = _project(
        keep_geom_types(layers.waterways, ["LineString", "MultiLineString"]), target_crs
    )
    water = _project(
        keep_geom_types(layers.water, ["Polygon", "MultiPolygon"]), target_crs
    )
    forest = _project(
        keep_geom_types(layers.forest, ["Polygon", "MultiPolygon"]), target_crs
    )
    wood = _project(
        keep_geom_types(layers.wood, ["Polygon", "MultiPolygon"]), target_crs
    )
    trees = _project(keep_geom_types(layers.trees, ["Point", "MultiPoint"]), target_crs)
    buildings = _project(
        keep_geom_types(layers.buildings, ["Polygon", "MultiPolygon"]), target_crs
    )

    route_buffered = route.buffer(buffer_meters)
    xmin, ymin, xmax, ymax = route_buffered.total_bounds
    extent = (xmin, xmax, ymin, ymax)

    return PreparedMap(
        route=route,
        places=places,
        major_roads=major_roads,
        minor_roads=minor_roads,
        waterways=waterways,
        water=water,
        forest=forest,
        wood=wood,
        trees=trees,
        buildings=buildings,
        target_crs=target_crs,
        extent=extent,
    )
