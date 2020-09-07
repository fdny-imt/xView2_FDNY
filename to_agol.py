import arcgis
import rasterio
import shapely.geometry

from rasterio.features import shapes
from shapely.geometry import Polygon, shape, MultiPolygon



# Enable .from_shapely for building AGOL features from shapely features.
@classmethod
def from_shapely(cls, shapely_geometry):
    return cls(shapely_geometry.__geo_interface__)

arcgis.geometry.BaseGeometry.from_shapely = from_shapely


def agol_arg_check(args):
    agol_args = [args.agol_user,
                 args.agol_password,
                 args.agol_dmg_feature_service,
                 args.agol_dmg_layer_num,
                 args.agol_centroid_feature_service,
                 args.agol_centroid_layer_num,
                 args.agol_aoi_feature_service,
                 args.agol_aoi_layer_num]

    if any([agol_args]):
        if not args.agol_user:
            print('Missing AGOL username. Skipping AGOL push.')
            return False
        elif not args.agol_password:
            print('Missing AGOL password. Skipping AGOL push.')
            return False
        elif not args.agol_dmg_feature_service:
            print('Missing AGOL damage feature service ID. Skipping AGOL push.')
            return False
        elif not args.agol_dmg_layer_num:
            print('Missing AGOL damage layer. Skipping AGOL push.')
            return False
        else:
            agol_push = [False, False]
    else:
        return False

    if all([args.agol_aoi_feature_service, args.agol_aoi_layer_num]):
        agol_push[0] = True

    if all([args.agol_centroid_feature_service, args.agol_centroid_layer_num]):
        agol_push[1] = True

    return agol_push


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


def create_aoi_poly(features):
    aoi_polys = [geom for geom, val in features]
    polys = MultiPolygon(aoi_polys)
    box = shapely.geometry.box(*polys.bounds)
    shape = arcgis.geometry.Geometry.from_shapely(box)
    poly = arcgis.features.Feature(shape, attributes={'status': 'complete'})

    aoi_poly = [poly]

    return aoi_poly


def create_centroids(features):
    centroids = []
    for geom, val in features:
        esri_shape = arcgis.geometry.Geometry.from_shapely(geom.centroid)
        new_cent = arcgis.features.Feature(esri_shape, attributes={'dmg': val})
        centroids.append(new_cent)

    return centroids


def create_damage_polys(polys):
    polygons = []
    for geom, val in polys:
        esri_shape = arcgis.geometry.Geometry.from_shapely(geom)
        feature = arcgis.features.Feature(esri_shape, attributes={'dmg': val})
        polygons.append(feature)

    return polygons


def agol_append(user, pw, src_feats, dest_fs, layer):
    gis = arcgis.gis.GIS(username=user, password=pw)
    layer = gis.content.get(dest_fs).layers[int(layer)]
    layer.edit_features(adds=src_feats, rollback_on_failure=True)

    return len(src_feats), layer.properties.name
