from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pencil_map.config import MapConfig
from pencil_map.drawing import (
    add_paper_texture,
    draw_places,
    draw_route_flag,
    draw_route_start,
    pencil_plot_lines,
    pencil_plot_points,
    pencil_plot_polygons,
    soften_geometry,
)
from pencil_map.io import route_endpoints
from pencil_map.layers import MapLayers, PreparedMap, prepare_layers


def render_pencil_map(
    route,
    places,
    layers: MapLayers,
    config: MapConfig | None = None,
):
    config = config or MapConfig()
    prepared = prepare_layers(
        route,
        places,
        layers,
        config.route_buffer_meters,
        aspect_ratio=config.figsize[0] / config.figsize[1],
    )
    return render_prepared_map(prepared, config)


def render_prepared_map(prepared: PreparedMap, config: MapConfig | None = None):
    config = config or MapConfig()
    rng = np.random.default_rng(config.random_seed)
    fig, ax = plt.subplots(figsize=config.figsize)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_position((0, 0, 1, 1))

    ax.set_xlim(prepared.extent[0], prepared.extent[1])
    ax.set_ylim(prepared.extent[2], prepared.extent[3])
    fig.patch.set_facecolor(config.paper_color)
    ax.set_facecolor(config.paper_color)

    add_paper_texture(ax, prepared.extent, rng)

    pencil_plot_polygons(
        ax,
        prepared.water,
        jitter_meters=config.pencil_jitter_meters,
        rng=rng,
        facecolor="#8fbfe0",
        edgecolor="#4f84a8",
        alpha=0.30,
    )

    if config.plot_woods:
        forest_soft = prepared.forest.copy()
        forest_soft["geometry"] = forest_soft.geometry.apply(
            lambda geom: soften_geometry(geom, 14)
        )
        wood_soft = prepared.wood.copy()
        wood_soft["geometry"] = wood_soft.geometry.apply(
            lambda geom: soften_geometry(geom, 14)
        )

        pencil_plot_polygons(
            ax,
            forest_soft,
            jitter_meters=config.pencil_jitter_meters,
            rng=rng,
            facecolor="#9fcb84",
            edgecolor="#86ad73",
            alpha=0.34,
            outline=False,
        )
        pencil_plot_polygons(
            ax,
            wood_soft,
            jitter_meters=config.pencil_jitter_meters,
            rng=rng,
            facecolor="#9fcb84",
            edgecolor="#86ad73",
            alpha=0.34,
            outline=False,
        )
        pencil_plot_points(
            ax,
            prepared.trees,
            jitter_meters=config.pencil_jitter_meters,
            rng=rng,
            color="#86ad73",
            size=8,
            alpha=0.28,
            passes=2,
        )
    pencil_plot_polygons(
        ax,
        prepared.buildings,
        jitter_meters=config.pencil_jitter_meters,
        rng=rng,
        facecolor="0.62",
        edgecolor="0.35",
        alpha=0.12,
    )
    pencil_plot_lines(
        ax,
        prepared.waterways,
        jitter_meters=config.pencil_jitter_meters,
        rng=rng,
        color="#4f84a8",
        linewidth=1.15,
        alpha=0.38,
        passes=4,
    )
    if config.plot_route:
        pencil_plot_lines(
            ax,
            prepared.route,
            jitter_meters=config.pencil_jitter_meters,
            rng=rng,
            color=config.route_color,
            linewidth=4.0,
            alpha=0.50,
            passes=6,
            zorder=20,
        )

        start_xy, end_xy = route_endpoints(prepared.route.geometry.iloc[0])
        if start_xy and end_xy:
            route_scale = max(
                prepared.extent[1] - prepared.extent[0],
                prepared.extent[3] - prepared.extent[2],
            )
            marker_size = route_scale * 0.02
            draw_route_start(ax, start_xy, config.route_color, marker_size)
            draw_route_flag(ax, end_xy, config.route_color, marker_size)

    draw_places(
        ax, prepared.places, route_color=config.route_color, image_dir=config.image_dir
    )

    if config.plot_minor_roads:
        pencil_plot_lines(
            ax,
            prepared.minor_roads,
            jitter_meters=config.pencil_jitter_meters,
            rng=rng,
            color="0.10",
            linewidth=0.95,
            alpha=0.34,
            passes=config.n_jitter_passes + 1,
        )

    pencil_plot_lines(
        ax,
        prepared.major_roads,
        jitter_meters=config.pencil_jitter_meters,
        rng=rng,
        color="0.10",
        linewidth=0.95,
        alpha=0.34,
        passes=config.n_jitter_passes + 1,
    )
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")
    return fig, ax


def save_pencil_map(fig, output_paths, *, dpi: int = 300):
    for output_path in output_paths:
        path = Path(output_path)
        if path.suffix.lower() == ".svg":
            fig.savefig(path)
        else:
            fig.savefig(path, dpi=dpi)
