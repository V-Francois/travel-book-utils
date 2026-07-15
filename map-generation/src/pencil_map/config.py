from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MapConfig:
    route_buffer_meters: int = 600
    route_color: str = "#F56F16"
    random_seed: int = 42
    n_jitter_passes: int = 3
    pencil_jitter_meters: float = 4
    figsize: tuple[int, int] = (10, 13)
    dpi: int = 300
    paper_color: str = "#fcfaf4"
    image_dir: Path | None = None
    plot_minor_roads: bool = False
    plot_woods: bool = True
    plot_route: bool = True
