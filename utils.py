import coloredlogs
import logging
from geopy import distance

coloredlogs.install()
logging.basicConfig(level=logging.INFO,
                    format='%(name)s - %(levelname)s - %(message)s - %(relativeCreated)d')


def divide_bbox(bbox):
    """
    dividing bounding box to 4 boxes with equal areas
    """
    [min_lon, min_lat, max_lon, max_lat] = bbox.split(',')
    cent_lon = (float(min_lon) + float(max_lon))/2.0
    cent_lat = (float(min_lat) + float(max_lat))/2.0

    return [f'{min_lon},{min_lat},{cent_lon},{cent_lat}',
            f'{cent_lon},{min_lat},{max_lon},{cent_lat}',
            f'{min_lon},{cent_lat},{cent_lon},{max_lat}',
            f'{cent_lon},{cent_lat},{max_lon},{max_lat}']


def get_area(bbox):
    bbox = [float(val) for val in bbox.split(',')]
    [min_lon, min_lat, max_lon, max_lat] = bbox
    coords_1 = (min_lat, min_lon)
    coords_2 = (max_lat, min_lon)
    length_1 = distance.distance(coords_1, coords_2).km
    coords_1 = (max_lat, min_lon)
    coords_2 = (max_lat, max_lon)
    length_2 = distance.distance(coords_1, coords_2).km
    area_in_km = (length_1 * length_2)
    return area_in_km
