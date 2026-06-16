import geopandas as gpd
import osmnx as ox
import svgwrite

from shapely.geometry import box
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon

# --------------------------------------------------
# REGION
# --------------------------------------------------

north = 47.6897
south = 47.5884
west = 3.66
east = 3.77

region = box(west, south, east, north)

# --------------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------------

tags = {"landuse": True, "natural": True}

print("Downloading land cover...")
land = ox.features_from_polygon(region, tags)

print("Downloading roads...")
graph = ox.graph_from_polygon(region, network_type="drive")

roads = ox.graph_to_gdfs(graph, nodes=False)

# --------------------------------------------------
# PROJECT TO METERS
# --------------------------------------------------

CRS = 3857

land = land.to_crs(CRS)
roads = roads.to_crs(CRS)

minx, miny, maxx, maxy = land.total_bounds

# --------------------------------------------------
# SVG SETTINGS
# --------------------------------------------------

WIDTH = 3000
HEIGHT = 3000

dwg = svgwrite.Drawing("map.svg", size=(WIDTH, HEIGHT))

# paper color
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#f7f2e8"))

# --------------------------------------------------
# COORD TRANSFORM
# --------------------------------------------------


def project(x, y):
    px = (x - minx) / (maxx - minx)
    py = (y - miny) / (maxy - miny)

    sx = px * WIDTH
    sy = HEIGHT - py * HEIGHT

    return sx, sy


# --------------------------------------------------
# COLORS
# --------------------------------------------------

FOREST = "#8ea879"
FARMLAND = "#d8cf9c"
WATER = "#a8c5d6"
RESIDENTIAL = "#ed8139"

colors = {
    "forest": FOREST,
    "tree": FOREST,
    "farmland": FARMLAND,
    "meadow": FARMLAND,
    "residential": RESIDENTIAL,
    "water": WATER,
    "reservoir": WATER,
}

# --------------------------------------------------
# DRAW POLYGONS
# --------------------------------------------------


def draw_polygon(poly, color):
    pts = [project(x, y) for x, y in poly.exterior.coords]

    dwg.add(dwg.polygon(pts, fill=color, stroke="none"))


# --------------------------------------------------
# LANDCOVER
# --------------------------------------------------

for _, row in land.iterrows():
    geom = row.geometry

    landuse = row.get("landuse")
    natural = row.get("natural")

    if landuse in colors.keys():
        color = colors[landuse]
    elif natural in colors.keys():
        color = colors[natural]
    else:
        continue

    if isinstance(geom, Polygon):
        draw_polygon(geom, color)

    elif isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            draw_polygon(poly, color)

# --------------------------------------------------
# ROADS
# --------------------------------------------------

for _, row in roads.iterrows():
    geom = row.geometry

    if geom.geom_type != "LineString":
        continue

    pts = [project(x, y) for x, y in geom.coords]

    dwg.add(
        dwg.polyline(
            pts,
            fill="none",
            stroke="#666666",
            stroke_width=1.2,
            stroke_linecap="round",
            stroke_linejoin="round",
        )
    )

# --------------------------------------------------
# SAVE
# --------------------------------------------------

dwg.save()

print("Saved map.svg")
