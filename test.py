import requests
import time
import logging
from geopy import distance



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
base_url = 'https://www.booking.com'
markers_on_map_url = base_url + '/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEJuAEZyAEM2AED6AEB-AECiAIBqAIDuALJ3LyYBsACAdICJGY0ZmExYzc2LTlmOGMtNGM0OC04YTA1LTkzYzc3NDdjZmEwY9gCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=311644e806e807a6&aid=304142&dest_type=country&sr_id=&ref=searchresults&limit=100&stype=1&lang=en-gb&ssm=1&sech=1&ngp=1&room1=A%2CA&maps_opened=1&esf=1&sr_lat=&sr_long=&dba=1&dbc=1&srh=191867%2C3016146%2C301272%2C6948254%2C51288%2C343954%2C301050%2C6478778%2C2337735%2C1357296%2C338044%2C451028%2C5390634%2C1420234%2C4373824%2C173909%2C1865108%2C238601%2C54257%2C542266%2C180434%2C361801%2C1105263%2C4246076%2C270718&somp=1&mdimb=1%20&tp=1%20&img_size=270x200%20&avl=1%20&nor=1%20&spc=1%20&rmd=1%20&slpnd=1%20&sbr=1&at=1%20&sat=1%20&ssu=1&srocc=1&nflt=ht_id%3D204;BBOX='
headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
hotels_urls = set()



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

def add_hotels_url_to_set(hotels):
    for hotel in hotels:
        link_hotel = hotel['b_url'].split(';')[0]
        if(link_hotel and link_hotel.split('hotel/')[1][0:2] == 'il'):
            hotel_url = base_url + link_hotel
            hotel_url = hotel_url.split('?')[0]
            hotels_urls.add(hotel_url)
            print(
                f'hotel number:{len(hotels_urls)} ,hotel url: {hotel_url}, time:{time.ctime()}') 

def getArea(bbox):
    bbox = [float(val) for val in bbox.split(',')]

    [min_lon, min_lat, max_lon, max_lat] = bbox

    coords_1 = (min_lat, min_lon)
    coords_2 = (min_lat, max_lon)

    length_1 = (distance.distance(coords_1, coords_2).km)

    coords_1 = (min_lat, max_lon)
    coords_2 = (max_lat, max_lon)

    length_2 = distance.distance(coords_1, coords_2).km

    area_in_km = (length_1 * length_2)
    return area_in_km

def recursive_divide_bbox(url):
    response= requests.get(url,headers= headers)
    print(response,'response')
    json_response = response.json()
    hotels = json_response['b_hotels']
    bbox = url.split('BBOX=')[1]
    area = getArea(bbox)
    if(len(hotels) <= 2 or area < 0.001):
        return
    add_hotels_url_to_set(hotels)
    bbox_list = divide_bbox(bbox)
    for bbox in bbox_list:
        recursive_divide_bbox(markers_on_map_url+bbox)


if __name__ == '__main__':
    start_time = time.time()
    logger.info(f"start scraping")
    recursive_divide_bbox(markers_on_map_url+'34.2654333839,29.5013261988,35.8363969256,33.2774264593')
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(total_time,"finish all in: ")
