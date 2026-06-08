import random
import numpy as np
import geopandas as gpd

from PIL import Image
from PIL import ImageDraw

from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon

WIDTH = 4000
HEIGHT = 4000

land = gpd.read_file("landcover.geojson")
roads = gpd.read_file("roads.geojson")

land = land.to_crs(3857)
roads = roads.to_crs(3857)

bounds = land.total_bounds

minx, miny, maxx, maxy = bounds

canvas = Image.new(
    "RGBA", (WIDTH, HEIGHT), (205, 200, 145, 255)
)  # (245, 242, 232, 255))

draw = ImageDraw.Draw(canvas, "RGBA")


def project(x, y):
    px = (x - minx) / (maxx - minx)
    py = (y - miny) / (maxy - miny)

    return (int(px * WIDTH), HEIGHT - int(py * HEIGHT))


def jitter_polygon(poly, amount=15):
    coords = []

    for x, y in poly.exterior.coords:
        coords.append(
            (x + random.uniform(-amount, amount), y + random.uniform(-amount, amount))
        )

    return Polygon(coords)


def watercolor_fill(poly, color, N=20):
    for _ in range(N):
        try:
            p = jitter_polygon(poly)

            pts = [project(x, y) for x, y in p.exterior.coords]

            draw.polygon(pts, fill=(*color, 12))

        except:
            pass


colors = {
    "forest": (110, 150, 105),
    "tree": (110, 150, 105),
    "farmland": (205, 200, 145),
    "meadow": (205, 200, 145),
    "residential": (0, 0, 255),
    "basin": "red",
    "water": (140, 180, 210),
    "reservoir": (140, 180, 210),
}

for _, row in land.iterrows():
    geom = row.geometry

    if geom is None:
        continue

    landuse = row.get("landuse")
    natural = row.get("natural")

    if landuse in colors.keys():
        color = colors[landuse]
    elif natural in colors.keys():
        color = colors[natural]
    else:
        continue

    polygons = []

    if isinstance(geom, Polygon):
        polygons = [geom]

    elif isinstance(geom, MultiPolygon):
        polygons = list(geom.geoms)

    for poly in polygons:
        watercolor_fill(poly, color)


for _, row in roads.iterrows():
    geom = row.geometry

    if geom.geom_type != "LineString":
        continue

    pts = [project(x, y) for x, y in geom.coords]

    draw.line(pts, fill=(90, 90, 90, 255), width=2)


canvas.save("watercolor_base.png")
