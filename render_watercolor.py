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


def make_noise_octave(width, height, cell_size):
    grid_w = max(2, width // cell_size + 2)
    grid_h = max(2, height // cell_size + 2)
    grid = np.random.rand(grid_h, grid_w).astype(np.float32)
    layer = Image.fromarray((grid * 255).astype(np.uint8), mode="L").resize(
        (width, height), resample=Image.Resampling.BICUBIC
    )
    return np.asarray(layer, dtype=np.float32)


def make_granulation_field(width, height):
    noise = (
        make_noise_octave(width, height, 220) * 0.36
        + make_noise_octave(width, height, 96) * 0.28
        + make_noise_octave(width, height, 42) * 0.22
        + make_noise_octave(width, height, 18) * 0.14
    )

    noise = (noise - noise.min()) / (np.ptp(noise) or 1.0)
    return (noise * 255).astype(np.uint8)


GRANULATION = make_granulation_field(WIDTH, HEIGHT)


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


def boost_color(color, saturation=1.12, value=1.03):
    r, g, b = color
    avg = (r + g + b) / 3.0
    r = avg + (r - avg) * saturation
    g = avg + (g - avg) * saturation
    b = avg + (b - avg) * saturation
    return clamp_color((r * value, g * value, b * value))


def tint_color(color, variation=12):
    r, g, b = color
    return clamp_color(
        (
            r + random.randint(-variation, variation),
            g + random.randint(-variation, variation),
            b + random.randint(-variation, variation),
        )
    )


def draw_geometry(geom, fill):
    if geom.is_empty:
        return

    if isinstance(geom, Polygon):
        draw.polygon([project(x, y) for x, y in geom.exterior.coords], fill=fill)
        return

    if isinstance(geom, MultiPolygon):
        for part in geom.geoms:
            draw_geometry(part, fill)


def granulation_fill(poly, color):
    # Use a coherent noise field so pigment clusters feel like watercolor granulation.
    area_scale = max(1.0, float(poly.area) / 500_000.0)
    samples = min(180, max(20, int(24 * area_scale)))
    max_radius = 2 + min(8, int(area_scale))

    for _ in range(samples):
        try:
            x, y = random_point_in_polygon(poly)
            px, py = project(x, y)
            if px < 0 or py < 0 or px >= WIDTH or py >= HEIGHT:
                continue

            noise_value = int(GRANULATION[py, px])
            if noise_value < 120:
                continue

            intensity = (noise_value - 120) / 135.0
            radius = random.randint(1, max_radius) + int(intensity * 4)
            pigment = boost_color(
                clamp_color(tuple(v * random.uniform(0.78, 0.94) for v in color)),
                saturation=random.uniform(1.02, 1.12),
                value=random.uniform(0.90, 1.0),
            )
            alpha = int(8 + intensity * 42)
            draw.ellipse(
                (px - radius, py - radius, px + radius, py + radius),
                fill=(*pigment, alpha),
            )
        except Exception:
            pass


def watercolor_fill(poly, color, N=18):
    # Build the wash from a few larger, translucent passes plus smaller
    # darker accents. That keeps each polygon from looking like a flat fill.
    passes = [
        (1.8, 24, 0.16),
        (1.0, 18, 0.22),
        (0.7, 12, 0.28),
    ]

    for scale, jitter, alpha in passes:
        try:
            p = poly.buffer(scale)
            if p.is_empty:
                p = poly

            for _ in range(max(1, N // 4)):
                q = jitter_polygon(p, amount=jitter)
                pts = [project(x, y) for x, y in q.exterior.coords]
                draw.polygon(
                    pts,
                    fill=(
                        *boost_color(tint_color(color, 14), 1.15, 1.04),
                        int(255 * alpha),
                    ),
                )
        except Exception:
            pass

    # A few darker veins create the watercolor edge pooling effect.
    for _ in range(max(2, N // 6)):
        try:
            p = jitter_polygon(poly, amount=8)
            pts = [project(x, y) for x, y in p.exterior.coords]
            shade = boost_color(
                clamp_color(tuple(v * random.uniform(0.84, 0.96) for v in color)),
                saturation=1.06,
                value=1.0,
            )
            draw.polygon(pts, fill=(*shade, random.randint(18, 35)))
        except Exception:
            pass

    # Darken the perimeter with a few thin interior rings derived from buffers.
    ring_widths = [18, 42, 78]
    ring_alphas = [42, 28, 16]
    ring_shades = [0.72, 0.82, 0.9]

    for width, alpha, shade_scale in zip(ring_widths, ring_alphas, ring_shades):
        try:
            inner = poly.buffer(-width)
            ring = (
                poly.difference(inner)
                if not inner.is_empty
                else poly.buffer(width).difference(poly)
            )
            ring = ring.buffer(0)
            ring_fill = boost_color(
                clamp_color(tuple(v * shade_scale for v in color)),
                saturation=1.05,
                value=0.92,
            )
            draw_geometry(ring, (*ring_fill, alpha))
        except Exception:
            pass

    granulation_fill(poly, color)


colors = {
    "forest": (88, 142, 86),
    "tree": (92, 146, 90),
    "farmland": (214, 189, 96),
    "meadow": (205, 182, 104),
    "residential": (204, 162, 150),
    "basin": (94, 158, 214),
    "water": (92, 160, 218),
    "reservoir": (90, 156, 214),
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

    draw.line(pts, fill=(112, 102, 92, 210), width=3)
    draw.line(pts, fill=(72, 66, 60, 120), width=1)


canvas.save("watercolor_base.png")
