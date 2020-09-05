import arcgis
import rasterio
from rasterio.features import shapes
from shapely.geometry import Polygon, shape


@classmethod
def from_shapely(cls, shapely_geometry):
    return cls(shapely_geometry.__geo_interface__)

arcgis.geometry.BaseGeometry.from_shapely = from_shapely


def create_polys(in_files):

    polygons = []
    for idx, f in enumerate(in_files):
        src = rasterio.open(f)
        crs = src.crs
        transform = src.transform

        bnd = src.read(1)
        polys = list(shapes(bnd, transform=transform))

        for geom, val in polys:
            if val == 0:
                continue
            polygons.append((Polygon(shape(geom)), val))

    return polygons


def get_feature_set(polys):
    polygons = []
    for geom, val in polys:
        esri_shape = arcgis.geometry.Geometry.from_shapely(geom)
        feature = arcgis.features.Feature(esri_shape, attributes={'dmg': val})
        polygons.append(feature)

    arcgis.features.FeatureSet(polygons)

    return polygons


def agol_append(user, pw, src_feats, dest_fs, layer):
    gis = arcgis.gis.GIS(username=user, password=pw)
    layer = gis.content.get(dest_fs).layers[layer]
    layer.edit_features(adds=src_feats, rollback_on_failure=True)

    return len(src_feats.features)
