#! /usr/bin/env python3.11
"""
Fetches official California state boundary from https://data.ca.gov/dataset/ca-geographic-boundaries and convert to a simplified polygon.
"""

import io
import os
import zipfile

import fiona
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from shapely import wkt
import requests

BASENAME = 'ca_state'
SIXTY_KM = 60_000


def main() -> None:

    get_data()

    with fiona.open(BASENAME) as shapefile:
        # we assume it has only a single feature
        feature = shapefile[0]
        print(feature)

        geom = shape(feature['geometry'])
        buffered = geom.buffer(SIXTY_KM)
        simple = buffered.simplify(SIXTY_KM)

        transformer = Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True)
        latlon_geometry = transform(transformer.transform, simple)

        ca_wkt = wkt.dumps(latlon_geometry, rounding_precision=1)
        print(ca_wkt)

        ca_geom = wkt.loads(ca_wkt)
        coords = list(map(list, ca_geom.exterior.coords))
        arcgis_geom = {
            'rings': [coords],
            'spatialReference': {'wkid': 4326}  # Use EPSG:4326 for WGS84 Lat/Lon
        }
        print(arcgis_geom)


def get_data() -> None:
    """If needed, fetch/extract the California polygon."""

    if os.path.exists(BASENAME):
        return

    url = f"https://data.ca.gov/dataset/e212e397-1277-4df3-8c22-40721b095f33/resource/3db1e426-fb51-44f5-82d5-a54d7c6e188b/download/{BASENAME}.zip"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"Failed to download {url}. Status code: {resp.status_code}")

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall(BASENAME)
        print(f"Extracted files: {z.namelist()}")


if __name__ == "__main__":
    main()
