import shutil
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString, Point


class PencilMapPackageTest(unittest.TestCase):
    def test_package_import_has_render_api(self):
        import pencil_map

        self.assertTrue(hasattr(pencil_map, "MapConfig"))
        self.assertTrue(hasattr(pencil_map, "MapLayers"))
        self.assertTrue(hasattr(pencil_map, "render_pencil_map"))
        self.assertTrue(hasattr(pencil_map, "scale_bbox_to_ratio"))

    def test_places_from_dataframe_uses_latitude_x_and_longitude_y(self):
        from pencil_map.io import places_from_dataframe

        places = places_from_dataframe(
            pd.DataFrame(
                {
                    "name": ["Town", "  ", None],
                    "x": [47.68, 47.60, 47.59],
                    "y": [3.67, 3.68, 3.76],
                    "img": ["", "", ""],
                }
            )
        )

        self.assertEqual(list(places["name"]), ["Town"])
        self.assertEqual(str(places.crs), "EPSG:4326")
        self.assertTrue(places.geometry.iloc[0].equals(Point(3.67, 47.68)))

    def test_route_from_gpx_reads_track_segments(self):
        from pencil_map.io import route_from_gpx

        tmp_path = Path(self._testMethodName)
        tmp_path.mkdir(exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(tmp_path, ignore_errors=True))
        gpx = tmp_path / "route.gpx"
        gpx.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="47.0" lon="3.0" />
    <trkpt lat="47.1" lon="3.1" />
  </trkseg></trk>
</gpx>
""",
            encoding="utf-8",
        )

        route = route_from_gpx(gpx)

        self.assertEqual(str(route.crs), "EPSG:4326")
        self.assertTrue(
            route.geometry.iloc[0].equals(LineString([(3.0, 47.0), (3.1, 47.1)]))
        )

    def test_concatenate_routes_preserves_order(self):
        from pencil_map.io import concatenate_routes

        combined = concatenate_routes(
            [
                LineString([(3.0, 47.0), (3.1, 47.1)]),
                LineString([(3.1, 47.1), (3.2, 47.2)]),
                MultiLineString(
                    [
                        LineString([(3.2, 47.2), (3.3, 47.3)]),
                        LineString([(3.3, 47.3), (3.4, 47.4)]),
                    ]
                ),
            ]
        )

        self.assertEqual(
            list(combined.coords),
            [
                (3.0, 47.0),
                (3.1, 47.1),
                (3.2, 47.2),
                (3.3, 47.3),
                (3.4, 47.4),
            ],
        )

    def test_concatenate_routes_accepts_geometry_array(self):
        from pencil_map.io import concatenate_routes

        routes = gpd.GeoSeries(
            [
                LineString([(3.0, 47.0), (3.1, 47.1)]),
                LineString([(3.1, 47.1), (3.2, 47.2)]),
            ],
            crs="EPSG:4326",
        )

        combined = concatenate_routes(routes.array)

        self.assertTrue(
            combined.equals(LineString([(3.0, 47.0), (3.1, 47.1), (3.2, 47.2)]))
        )

    def test_bbox_from_route_returns_lon_lat_order(self):
        from pencil_map.layers import bbox_from_route

        route = gpd.GeoDataFrame(
            geometry=[LineString([(3.0, 47.0), (3.1, 47.1)])], crs="EPSG:4326"
        )

        minx, miny, maxx, maxy = bbox_from_route(route, buffer_meters=100)

        self.assertLess(minx, 3.0)
        self.assertLess(miny, 47.0)
        self.assertGreater(maxx, 3.1)
        self.assertGreater(maxy, 47.1)

    def test_scale_bbox_to_ratio_stretches_width_without_cropping(self):
        from pencil_map.layers import scale_bbox_to_ratio

        bbox = (0.0, 0.0, 2.0, 2.0)

        scaled = scale_bbox_to_ratio(bbox, 2.0)

        self.assertEqual(scaled, (-1.0, 0.0, 3.0, 2.0))

    def test_scale_bbox_to_ratio_stretches_height_without_cropping(self):
        from pencil_map.layers import scale_bbox_to_ratio

        bbox = (0.0, 0.0, 4.0, 2.0)

        scaled = scale_bbox_to_ratio(bbox, 1.0)

        self.assertEqual(scaled, (0.0, -1.0, 4.0, 3.0))

    def test_scale_bbox_to_ratio_keeps_matching_bbox(self):
        from pencil_map.layers import scale_bbox_to_ratio

        bbox = (0.0, 0.0, 4.0, 2.0)

        scaled = scale_bbox_to_ratio(bbox, 2.0)

        self.assertEqual(scaled, bbox)

    def test_prepare_layers_projects_and_splits_major_roads(self):
        from pencil_map.layers import MapLayers, PreparedMap, prepare_layers

        route = gpd.GeoDataFrame(
            geometry=[LineString([(3.0, 47.0), (3.01, 47.01)])], crs="EPSG:4326"
        )
        roads = gpd.GeoDataFrame(
            {
                "highway": ["primary", "residential"],
                "geometry": [
                    LineString([(3.0, 47.0), (3.01, 47.01)]),
                    LineString([(3.0, 47.01), (3.01, 47.0)]),
                ],
            },
            crs="EPSG:4326",
        )
        places = gpd.GeoDataFrame(
            {"name": ["Town"]}, geometry=[Point(3.0, 47.0)], crs="EPSG:4326"
        )

        prepared = prepare_layers(
            route, places, MapLayers(roads=roads), buffer_meters=100
        )

        self.assertIsInstance(prepared, PreparedMap)
        self.assertEqual(len(prepared.major_roads), 1)
        self.assertEqual(len(prepared.minor_roads), 1)
        self.assertEqual(prepared.route.crs, prepared.target_crs)
        self.assertLess(prepared.extent[0], prepared.extent[1])


if __name__ == "__main__":
    unittest.main()
