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
    "RGBA", (WIDTH, HEIGHT), (228, 223, 200, 255)
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


def clamp_color(value):
    return tuple(max(0, min(255, int(v))) for v in value)


def tint_color(color, variation=12):
    r, g, b = color
    return clamp_color(
        (
            r + random.randint(-variation, variation),
            g + random.randint(-variation, variation),
            b + random.randint(-variation, variation),
        )
    )


def watercolor_fill(poly, color, N=18):
    # Build the wash from a few larger, translucent passes plus smaller
    # darker accents. That keeps each polygon from looking like a flat fill.
    passes = [
        (1.8, 24, 0.12),
        (1.0, 18, 0.18),
        (0.7, 12, 0.22),
    ]

    for scale, jitter, alpha in passes:
        try:
            p = poly.buffer(scale)
            if p.is_empty:
                p = poly

            for _ in range(max(1, N // 4)):
                q = jitter_polygon(p, amount=jitter)
                pts = [project(x, y) for x, y in q.exterior.coords]
                draw.polygon(pts, fill=(*tint_color(color, 18), int(255 * alpha)))
        except Exception:
            pass

    # A few darker veins create the watercolor edge pooling effect.
    for _ in range(max(2, N // 6)):
        try:
            p = jitter_polygon(poly, amount=8)
            pts = [project(x, y) for x, y in p.exterior.coords]
            shade = clamp_color(tuple(v * random.uniform(0.82, 0.95) for v in color))
            draw.polygon(pts, fill=(*shade, random.randint(18, 35)))
        except Exception:
            pass


colors = {
    "forest": (93, 135, 92),
    "tree": (96, 139, 95),
    "farmland": (202, 188, 122),
    "meadow": (192, 180, 126),
    "residential": (198, 170, 160),
    "basin": (120, 165, 205),
    "water": (118, 165, 205),
    "reservoir": (116, 162, 202),
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
        # Finer polygons need fewer passes; the jitter already creates texture.
        watercolor_fill(poly, color)


for _, row in roads.iterrows():
    geom = row.geometry

    if geom.geom_type != "LineString":
        continue

    pts = [project(x, y) for x, y in geom.coords]

    draw.line(pts, fill=(105, 100, 95, 200), width=3)
    draw.line(pts, fill=(70, 65, 60, 110), width=1)


canvas.save("watercolor_base.png")
