from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)


def jitter_coords(coords, amount, rng):
    return [(x + rng.normal(0, amount), y + rng.normal(0, amount)) for x, y in coords]


def jitter_geometry(geom, amount, rng):
    if geom is None or geom.is_empty:
        return geom

    if isinstance(geom, LineString):
        if len(geom.coords) < 2:
            return geom
        return LineString(jitter_coords(geom.coords, amount, rng))

    if isinstance(geom, MultiLineString):
        return MultiLineString(
            [
                jitter_geometry(part, amount, rng)
                for part in geom.geoms
                if len(part.coords) >= 2
            ]
        )

    if isinstance(geom, Polygon):
        exterior = jitter_coords(geom.exterior.coords, amount, rng)
        interiors = [jitter_coords(ring.coords, amount, rng) for ring in geom.interiors]
        return Polygon(exterior, interiors)

    if isinstance(geom, MultiPolygon):
        return MultiPolygon([jitter_geometry(part, amount, rng) for part in geom.geoms])

    if isinstance(geom, Point):
        return Point(geom.x + rng.normal(0, amount), geom.y + rng.normal(0, amount))

    if isinstance(geom, MultiPoint):
        return MultiPoint([jitter_geometry(part, amount, rng) for part in geom.geoms])

    return geom


def pencil_plot_lines(
    ax,
    gdf,
    *,
    jitter_meters,
    rng,
    color="0.15",
    linewidth=0.7,
    alpha=0.35,
    passes=3,
    zorder=5,
):
    if gdf.empty:
        return

    for _ in range(passes):
        sketch = gdf.copy()
        sketch["geometry"] = sketch.geometry.apply(
            lambda geom: jitter_geometry(geom, jitter_meters, rng)
        )
        sketch.plot(ax=ax, color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)


def pencil_plot_points(
    ax, gdf, *, jitter_meters, rng, color="0.15", size=8, alpha=0.3, passes=2
):
    if gdf.empty:
        return

    for _ in range(passes):
        sketch = gdf.copy()
        sketch["geometry"] = sketch.geometry.apply(
            lambda geom: jitter_geometry(geom, jitter_meters, rng)
        )

        xs = []
        ys = []
        for geom in sketch.geometry:
            if isinstance(geom, Point):
                xs.append(geom.x)
                ys.append(geom.y)
            elif isinstance(geom, MultiPoint):
                for pt in geom.geoms:
                    xs.append(pt.x)
                    ys.append(pt.y)

        if xs:
            ax.scatter(xs, ys, s=size, c=color, alpha=alpha, zorder=4, linewidths=0)


def soften_geometry(geom, amount=10):
    if geom is None or geom.is_empty:
        return geom
    softened = geom.buffer(-amount).buffer(amount)
    return softened if not softened.is_empty else geom


def pencil_plot_polygons(
    ax,
    gdf,
    *,
    jitter_meters,
    rng,
    facecolor="0.9",
    edgecolor="0.25",
    alpha=0.28,
    outline=True,
):
    if gdf.empty:
        return

    base = gdf.copy()
    base.plot(ax=ax, facecolor=facecolor, edgecolor="none", alpha=alpha, zorder=1)

    if not outline:
        return

    outlines = gdf.copy()
    outlines["geometry"] = outlines.geometry.boundary
    pencil_plot_lines(
        ax,
        outlines,
        jitter_meters=jitter_meters,
        rng=rng,
        color=edgecolor,
        linewidth=0.45,
        alpha=0.25,
        passes=2,
    )


def draw_route_start(ax, xy, color, size):
    x, y = xy
    ax.scatter([x], [y], s=size * 1.3, c=color, alpha=0.95, zorder=30, linewidths=0)
    ax.scatter([x], [y], s=size * 0.45, c="#fcfaf4", alpha=1.0, zorder=31, linewidths=0)


def draw_route_flag(ax, xy, color, size):
    x, y = xy
    pole_h = size * 1.8
    flag_w = size * 1.15
    flag_h = size * 0.9

    ax.plot([x, x], [y, y + pole_h], color="black", linewidth=1.8, zorder=30)
    pennant = mpatches.Polygon(
        [
            [x, y + pole_h],
            [x + flag_w, y + pole_h - flag_h * 0.35],
            [x, y + pole_h - flag_h],
        ],
        closed=True,
        facecolor=color,
        edgecolor="black",
        zorder=31,
    )
    ax.add_patch(pennant)


def label_place(ax, x, y, text, color, fontsize=16):
    ax.text(
        x,
        y,
        text,
        color=color,
        fontsize=fontsize,
        ha="center",
        va="center",
        zorder=40,
        path_effects=[
            path_effects.Stroke(linewidth=5, foreground="#fcfaf4", alpha=0.92),
            path_effects.Normal(),
        ],
    )


def draw_place_dot(ax, x, y, color, size=180):
    ax.scatter([x], [y], s=size, c=color, alpha=0.95, zorder=40, linewidths=0)


def add_place_image(ax, x, y, img_name, image_dir: Path, width_px=120):
    img_path = image_dir / str(img_name).strip()
    if not img_path.is_file():
        return False

    from PIL import Image

    pil_image = Image.open(img_path).convert("RGBA")
    height_px = max(1, int(round(width_px * pil_image.size[1] / pil_image.size[0])))
    resample = getattr(Image, "Resampling", Image).LANCZOS
    pil_image = pil_image.resize((width_px, height_px), resample)
    image = np.asarray(pil_image)

    ab = AnnotationBbox(
        OffsetImage(image, zoom=1),
        (x, y),
        frameon=False,
        box_alignment=(0.5, 0.5),
        zorder=40,
    )
    ax.add_artist(ab)
    return True


def draw_places(ax, places, *, route_color, image_dir: Path | None):
    for _, row in places.iterrows():
        name = str(row.get("name", "")).strip()
        if name == "nan":
            name = ""
        img_name = row.get("img")
        has_image = image_dir and pd.notna(img_name) and str(img_name).strip()
        if has_image and add_place_image(
            ax, row.geometry.x, row.geometry.y, img_name, image_dir
        ):
            continue
        if name:
            label_place(
                ax, row.geometry.x, row.geometry.y, name, color="#3f2d1f", fontsize=22
            )
        else:
            draw_place_dot(ax, row.geometry.x, row.geometry.y, route_color)


def add_paper_texture(ax, extent, rng):
    xmin, xmax, ymin, ymax = extent
    noise = rng.normal(0.92, 0.028, (1400, 1400))
    noise = np.clip(noise, 0, 1)
    ax.imshow(
        noise,
        extent=[xmin, xmax, ymin, ymax],
        cmap="gray",
        alpha=0.22,
        zorder=0,
        origin="lower",
    )


def draw_border(ax, extent, crs, *, jitter_meters, rng):
    border = gpd.GeoDataFrame(
        geometry=[
            Polygon(
                [
                    (extent[0], extent[2]),
                    (extent[1], extent[2]),
                    (extent[1], extent[3]),
                    (extent[0], extent[3]),
                    (extent[0], extent[2]),
                ]
            ).boundary
        ],
        crs=crs,
    )
    pencil_plot_lines(
        ax,
        border,
        jitter_meters=jitter_meters,
        rng=rng,
        color="0.12",
        linewidth=1.0,
        alpha=0.35,
        passes=3,
    )
