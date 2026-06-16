import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import (
    LineString,
    MultiLineString,
    Polygon,
    MultiPolygon,
    Point,
    MultiPoint,
)
from shapely.ops import transform


# ----------------------------
# Area: your bounding box
# ----------------------------
north = 47.6897
south = 47.5884
west = 3.66
east = 3.77

bbox = (west, south, east, north)  # OSMnx 2.x: left, bottom, right, top


# ----------------------------
# Styling controls
# ----------------------------
RANDOM_SEED = 42
N_JITTER_PASSES = 3
PENCIL_JITTER_METERS = 2
FIGSIZE = (10, 13)
DPI = 300

np.random.seed(RANDOM_SEED)


def safe_features_from_bbox(tags):
    try:
        gdf = ox.features_from_bbox(bbox, tags)
        if gdf.empty:
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        return gdf
    except Exception as e:
        print(f"Could not fetch {tags}: {e}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


def keep_geom_types(gdf, geom_types):
    if gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.isin(geom_types)].copy()


def jitter_coords(coords, amount):
    return [
        (x + np.random.normal(0, amount), y + np.random.normal(0, amount))
        for x, y in coords
    ]


def jitter_geometry(geom, amount):
    """
    Jitter geometry in projected units, here meters.
    Works best after projection to a metric CRS.
    """
    if geom is None or geom.is_empty:
        return geom

    if isinstance(geom, LineString):
        if len(geom.coords) < 2:
            return geom
        return LineString(jitter_coords(geom.coords, amount))

    if isinstance(geom, MultiLineString):
        return MultiLineString(
            [
                jitter_geometry(part, amount)
                for part in geom.geoms
                if len(part.coords) >= 2
            ]
        )

    if isinstance(geom, Polygon):
        exterior = jitter_coords(geom.exterior.coords, amount)
        interiors = [jitter_coords(ring.coords, amount) for ring in geom.interiors]
        return Polygon(exterior, interiors)

    if isinstance(geom, MultiPolygon):
        return MultiPolygon([jitter_geometry(part, amount) for part in geom.geoms])

    if isinstance(geom, Point):
        return Point(
            geom.x + np.random.normal(0, amount), geom.y + np.random.normal(0, amount)
        )

    if isinstance(geom, MultiPoint):
        return MultiPoint([jitter_geometry(part, amount) for part in geom.geoms])

    return geom


def pencil_plot_lines(ax, gdf, color="0.15", linewidth=0.7, alpha=0.35, passes=3):
    if gdf.empty:
        return

    for _ in range(passes):
        sketch = gdf.copy()
        sketch["geometry"] = sketch.geometry.apply(
            lambda g: jitter_geometry(g, PENCIL_JITTER_METERS)
        )
        sketch.plot(ax=ax, color=color, linewidth=linewidth, alpha=alpha, zorder=5)


def pencil_plot_polygons(ax, gdf, facecolor="0.9", edgecolor="0.25", alpha=0.28):
    if gdf.empty:
        return

    base = gdf.copy()
    base.plot(ax=ax, facecolor=facecolor, edgecolor="none", alpha=alpha, zorder=1)

    # sketchy polygon outlines
    outlines = gdf.copy()
    outlines["geometry"] = outlines.geometry.boundary
    pencil_plot_lines(
        ax, outlines, color=edgecolor, linewidth=0.45, alpha=0.25, passes=2
    )


def add_paper_texture(ax, extent):
    """
    Simple procedural paper texture: faint grayscale noise.
    """
    xmin, xmax, ymin, ymax = extent
    noise = np.random.normal(0.88, 0.035, (1400, 1400))
    noise = np.clip(noise, 0, 1)

    ax.imshow(
        noise,
        extent=[xmin, xmax, ymin, ymax],
        cmap="gray",
        alpha=0.22,
        zorder=0,
        origin="lower",
    )


# ----------------------------
# Download data
# ----------------------------
print("Downloading roads...")
G = ox.graph_from_bbox(bbox, network_type="all", simplify=True)
roads = ox.graph_to_gdfs(G, nodes=False, edges=True)

print("Downloading rivers/streams...")
waterways = safe_features_from_bbox({"waterway": ["river", "stream", "canal", "drain"]})

print("Downloading water bodies...")
water = safe_features_from_bbox({"natural": "water", "water": True})

print("Downloading buildings...")
buildings = safe_features_from_bbox({"building": True})

# print("Downloading points of interest...")
# pois = safe_features_from_bbox(
#    {
#        "amenity": [
#            "cafe",
#            "restaurant",
#            "bar",
#            "school",
#            "townhall",
#            "place_of_worship",
#            "parking",
#            "library",
#        ],
#        "tourism": ["museum", "attraction", "viewpoint", "hotel"],
#        "historic": True,
#    }
# )


# ----------------------------
# Prepare layers
# ----------------------------
roads = roads[["geometry", "highway"]].copy()
roads = roads.set_crs("EPSG:4326", allow_override=True)

waterways = keep_geom_types(waterways, ["LineString", "MultiLineString"])
water = keep_geom_types(water, ["Polygon", "MultiPolygon"])
buildings = keep_geom_types(buildings, ["Polygon", "MultiPolygon"])
# pois = keep_geom_types(pois, ["Point", "MultiPoint"])

# Use local projected CRS so jitter is in meters
all_for_crs = gpd.GeoDataFrame(geometry=list(roads.geometry), crs="EPSG:4326")
target_crs = all_for_crs.estimate_utm_crs()

roads = roads.to_crs(target_crs)
waterways = waterways.to_crs(target_crs)
water = water.to_crs(target_crs)
buildings = buildings.to_crs(target_crs)
# pois = pois.to_crs(target_crs)


# Split major/minor roads
def is_major(highway):
    if isinstance(highway, list):
        vals = highway
    else:
        vals = [highway]
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
    return any(v in major_types for v in vals)


roads["is_major"] = roads["highway"].apply(is_major)
major_roads = roads[roads["is_major"]].copy()
minor_roads = roads[~roads["is_major"]].copy()


# ----------------------------
# Draw
# ----------------------------
fig, ax = plt.subplots(figsize=FIGSIZE)

xmin, ymin, xmax, ymax = roads.total_bounds
pad_x = (xmax - xmin) * 0.04
pad_y = (ymax - ymin) * 0.04
extent = (xmin - pad_x, xmax + pad_x, ymin - pad_y, ymax + pad_y)

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

fig.patch.set_facecolor("#f7f2e8")
ax.set_facecolor("#f7f2e8")

add_paper_texture(ax, extent)

# Water bodies: pale pencil fill
pencil_plot_polygons(ax, water, facecolor="0.82", edgecolor="0.25", alpha=0.22)

# Buildings: faint graphite blocks
pencil_plot_polygons(ax, buildings, facecolor="0.62", edgecolor="0.35", alpha=0.12)

# Waterways
pencil_plot_lines(ax, waterways, color="0.30", linewidth=1.15, alpha=0.32, passes=4)

# Roads
pencil_plot_lines(
    ax, minor_roads, color="0.20", linewidth=0.42, alpha=0.28, passes=N_JITTER_PASSES
)

pencil_plot_lines(
    ax,
    major_roads,
    color="0.10",
    linewidth=0.95,
    alpha=0.34,
    passes=N_JITTER_PASSES + 1,
)

# POIs as tiny hand-drawn dots/circles
# if not pois.empty:
#    for _ in range(2):
#        sketch_pois = pois.copy()
#        sketch_pois["geometry"] = sketch_pois.geometry.apply(
#            lambda g: jitter_geometry(g, PENCIL_JITTER_METERS * 1.3)
#        )
#        sketch_pois.plot(ax=ax, color="0.12", markersize=8, alpha=0.30, zorder=10)

# Border rectangle, slightly jittered
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
    crs=target_crs,
)
pencil_plot_lines(ax, border, color="0.12", linewidth=1.0, alpha=0.35, passes=3)

ax.set_axis_off()
ax.set_aspect("equal")

plt.tight_layout(pad=0)

plt.savefig("pencil_map.png", dpi=DPI, bbox_inches="tight", pad_inches=0.05)
plt.savefig("pencil_map.svg", bbox_inches="tight", pad_inches=0.05)

print("Saved pencil_map.png and pencil_map.svg")
