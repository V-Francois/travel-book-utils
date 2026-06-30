import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString


def empty_wgs84_gdf() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


def route_from_gpx(path: str | Path) -> gpd.GeoDataFrame:
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        raise ValueError(f"Could not read GPX route from {path}") from exc

    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    segments = []

    for trkseg in root.findall(".//g:trkseg", ns):
        coords = [
            (float(trkpt.attrib["lon"]), float(trkpt.attrib["lat"]))
            for trkpt in trkseg.findall("g:trkpt", ns)
        ]
        if len(coords) >= 2:
            segments.append(LineString(coords))

    if not segments:
        return empty_wgs84_gdf()

    geometry = segments[0] if len(segments) == 1 else MultiLineString(segments)
    return gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")


def route_endpoints(geom):
    if isinstance(geom, LineString):
        coords = list(geom.coords)
        return coords[0], coords[-1]

    if isinstance(geom, MultiLineString):
        first = list(geom.geoms[0].coords)[0]
        last = list(geom.geoms[-1].coords)[-1]
        return first, last

    return None, None


def _route_parts(geom):
    if isinstance(geom, LineString):
        return [geom]
    if isinstance(geom, MultiLineString):
        return list(geom.geoms)
    raise TypeError(f"Unsupported route geometry: {geom.geom_type}")


def concatenate_routes(routes) -> LineString:
    coords = []

    for route in routes:
        for part in _route_parts(route):
            part_coords = list(part.coords)
            if not part_coords:
                continue
            if coords and coords[-1] == part_coords[0]:
                coords.extend(part_coords[1:])
            else:
                coords.extend(part_coords)

    if len(coords) < 2:
        raise ValueError("At least two route coordinates are required")

    return LineString(coords)


def places_from_dataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    if df.empty or not {"name", "x", "y"}.issubset(df.columns):
        return empty_wgs84_gdf()

    # Input CSV convention: x is latitude, y is longitude.
    data = df.copy()
    data["name"] = data["name"].astype(str).str.strip()
    if data.empty:
        return empty_wgs84_gdf()

    geometry = gpd.points_from_xy(data["y"], data["x"])
    return gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")


def places_from_csv(path: str | Path) -> gpd.GeoDataFrame:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise ValueError(f"Could not read places CSV from {path}") from exc
    return places_from_dataframe(df)
