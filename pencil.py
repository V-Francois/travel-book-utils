import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET

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
ROUTE_BUFFER_METERS = 600
ROUTE_COLOR = "#F56F16"  # Ochre


# ----------------------------
# Styling controls
# ----------------------------
RANDOM_SEED = 42
N_JITTER_PASSES = 3
PENCIL_JITTER_METERS = 4
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


def route_from_gpx(path):
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    segments = []

    for trkseg in root.findall(".//g:trkseg", ns):
        coords = []
        for trkpt in trkseg.findall("g:trkpt", ns):
            coords.append((float(trkpt.attrib["lon"]), float(trkpt.attrib["lat"])))
        if len(coords) >= 2:
            segments.append(LineString(coords))

    if not segments:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

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


def places_from_csv(path):
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    if df.empty or not {"name", "x", "y"}.issubset(df.columns):
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    # CSV uses x=latitude and y=longitude.
    geometry = gpd.points_from_xy(df["y"], df["x"])
    gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")
    gdf["name"] = gdf["name"].astype(str).str.strip()
    return gdf[gdf["name"] != ""].copy()


def bbox_from_route(route_gdf, buffer_meters):
    if route_gdf.empty:
        return None

    buffered = route_gdf.to_crs(route_gdf.estimate_utm_crs()).buffer(buffer_meters)
    minx, miny, maxx, maxy = buffered.to_crs("EPSG:4326").total_bounds
    return (minx, miny, maxx, maxy)


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


def pencil_plot_lines(
    ax, gdf, color="0.15", linewidth=0.7, alpha=0.35, passes=3, zorder=5
):
    if gdf.empty:
        return

    for _ in range(passes):
        sketch = gdf.copy()
        sketch["geometry"] = sketch.geometry.apply(
            lambda g: jitter_geometry(g, PENCIL_JITTER_METERS)
        )
        sketch.plot(ax=ax, color=color, linewidth=linewidth, alpha=alpha, zorder=zorder)


def pencil_plot_points(ax, gdf, color="0.15", size=8, alpha=0.3, passes=2):
    if gdf.empty:
        return

    for _ in range(passes):
        sketch = gdf.copy()
        sketch["geometry"] = sketch.geometry.apply(
            lambda g: jitter_geometry(g, PENCIL_JITTER_METERS)
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

    # Smooth sharp polygon corners by shrinking and re-expanding the shape.
    softened = geom.buffer(-amount).buffer(amount)
    return softened if not softened.is_empty else geom


def pencil_plot_polygons(
    ax, gdf, facecolor="0.9", edgecolor="0.25", alpha=0.28, outline=True
):
    if gdf.empty:
        return

    base = gdf.copy()
    base.plot(ax=ax, facecolor=facecolor, edgecolor="none", alpha=alpha, zorder=1)

    if not outline:
        return

    # sketchy polygon outlines
    outlines = gdf.copy()
    outlines["geometry"] = outlines.geometry.boundary
    pencil_plot_lines(
        ax, outlines, color=edgecolor, linewidth=0.45, alpha=0.25, passes=2
    )


def draw_route_start(ax, xy, color, size):
    x, y = xy
    ax.scatter([x], [y], s=size * 1.3, c=color, alpha=0.95, zorder=30, linewidths=0)
    ax.scatter(
        [x],
        [y],
        s=size * 0.45,
        c="#fcfaf4",
        alpha=1.0,
        zorder=31,
        linewidths=0,
    )


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


def add_paper_texture(ax, extent):
    """
    Simple procedural paper texture: faint grayscale noise.
    """
    xmin, xmax, ymin, ymax = extent
    noise = np.random.normal(0.92, 0.028, (1400, 1400))
    noise = np.clip(noise, 0, 1)

    ax.imshow(
        noise,
        extent=[xmin, xmax, ymin, ymax],
        cmap="gray",
        alpha=0.22,
        zorder=0,
        origin="lower",
    )


print("Loading route...")
route = route_from_gpx("route.gpx")
bbox = bbox_from_route(route, ROUTE_BUFFER_METERS)
if bbox is None:
    raise RuntimeError("route.gpx did not contain any track points")

print("Loading places...")
places = places_from_csv("places.csv")


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

print("Downloading forests/trees...")
forest = safe_features_from_bbox({"landuse": "forest"})
wood = safe_features_from_bbox({"natural": "wood"})
trees = safe_features_from_bbox({"natural": "tree"})

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
forest = keep_geom_types(forest, ["Polygon", "MultiPolygon"])
wood = keep_geom_types(wood, ["Polygon", "MultiPolygon"])
trees = keep_geom_types(trees, ["Point", "MultiPoint"])
route = keep_geom_types(route, ["LineString", "MultiLineString"])
buildings = keep_geom_types(buildings, ["Polygon", "MultiPolygon"])
# pois = keep_geom_types(pois, ["Point", "MultiPoint"])

# Use local projected CRS so jitter is in meters
target_crs = route.estimate_utm_crs()

roads = roads.to_crs(target_crs)
waterways = waterways.to_crs(target_crs)
water = water.to_crs(target_crs)
forest = forest.to_crs(target_crs)
wood = wood.to_crs(target_crs)
trees = trees.to_crs(target_crs)
route = route.to_crs(target_crs)
places = places.to_crs(target_crs)
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

route_buffered = route.to_crs(target_crs).buffer(ROUTE_BUFFER_METERS)
xmin, ymin, xmax, ymax = route_buffered.total_bounds
extent = (xmin, xmax, ymin, ymax)

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

fig.patch.set_facecolor("#fcfaf4")
ax.set_facecolor("#fcfaf4")

add_paper_texture(ax, extent)

# Water bodies: blue fill
pencil_plot_polygons(ax, water, facecolor="#8fbfe0", edgecolor="#4f84a8", alpha=0.30)

# Forests and trees: light green fill
forest_soft = forest.copy()
forest_soft["geometry"] = forest_soft.geometry.apply(lambda g: soften_geometry(g, 14))
wood_soft = wood.copy()
wood_soft["geometry"] = wood_soft.geometry.apply(lambda g: soften_geometry(g, 14))

pencil_plot_polygons(
    ax, forest_soft, facecolor="#9fcb84", edgecolor="#86ad73", alpha=0.34, outline=False
)
pencil_plot_polygons(
    ax, wood_soft, facecolor="#9fcb84", edgecolor="#86ad73", alpha=0.34, outline=False
)
pencil_plot_points(ax, trees, color="#86ad73", size=8, alpha=0.28, passes=2)

# Buildings: faint graphite blocks
pencil_plot_polygons(ax, buildings, facecolor="0.62", edgecolor="0.35", alpha=0.12)

# Waterways
pencil_plot_lines(ax, waterways, color="#4f84a8", linewidth=1.15, alpha=0.38, passes=4)

# Route: wide dark ochre pencil path
pencil_plot_lines(
    ax, route, color=ROUTE_COLOR, linewidth=4.0, alpha=0.50, passes=6, zorder=20
)

route_geom = route.geometry.iloc[0]
start_xy, end_xy = route_endpoints(route_geom)
if start_xy and end_xy:
    route_scale = max(extent[1] - extent[0], extent[3] - extent[2])
    marker_size = route_scale * 0.02
    draw_route_start(ax, start_xy, ROUTE_COLOR, marker_size)
    draw_route_flag(ax, end_xy, ROUTE_COLOR, marker_size)

for _, row in places.iterrows():
    fontsize = 22
    label_place(
        ax,
        row.geometry.x,
        row.geometry.y,
        row["name"],
        color="#3f2d1f",
        fontsize=fontsize,
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
