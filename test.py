import requests
from time import time
from utils import logging, get_area, divide_bbox
import os
from bs4 import BeautifulSoup
from geojson import Feature, Point, FeatureCollection, dump
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from hotel_data import HotelData

base_url = 'https://www.booking.com'
markers_on_map_url = base_url + '/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEJuAEZyAEM2AED6AEB-AECiAIBqAIDuALJ3LyYBsACAdICJGY0ZmExYzc2LTlmOGMtNGM0OC04YTA1LTkzYzc3NDdjZmEwY9gCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=311644e806e807a6&aid=304142&dest_type=country&sr_id=&ref=searchresults&limit=100&stype=1&lang=en-gb&ssm=1&sech=1&ngp=1&room1=A%2CA&maps_opened=1&esf=1&sr_lat=&sr_long=&dba=1&dbc=1&srh=191867%2C3016146%2C301272%2C6948254%2C51288%2C343954%2C301050%2C6478778%2C2337735%2C1357296%2C338044%2C451028%2C5390634%2C1420234%2C4373824%2C173909%2C1865108%2C238601%2C54257%2C542266%2C180434%2C361801%2C1105263%2C4246076%2C270718&somp=1&mdimb=1%20&tp=1%20&img_size=270x200%20&avl=1%20&nor=1%20&spc=1%20&rmd=1%20&slpnd=1%20&sbr=1&at=1%20&sat=1%20&ssu=1&srocc=1&nflt=ht_id%3D204;BBOX='
headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
hotels_urls = set()
logger = logging.getLogger(__name__)

def add_hotels_url_to_set(hotels):
    for hotel in hotels:
        link_hotel = hotel['b_url'].split(';')[0]
        if(link_hotel and link_hotel.split('hotel/')[1][0:2] == 'il'):
            hotel_url = base_url + link_hotel
            hotel_url = hotel_url.split('?')[0]
            hotels_urls.add(hotel_url)
            logger.info(
                f'hotel number:{len(hotels_urls)} ,hotel url: {hotel_url}')


def recursive_divide_bbox(url):
    response = requests.get(url, headers=headers)
    json_response = response.json()
    hotels = json_response['b_hotels']
    bbox = url.split('BBOX=')[1]
    area = get_area(bbox)
    if(len(hotels) <= 1 or area < 0.01):
        return
    add_hotels_url_to_set(hotels)
    bbox_list = divide_bbox(bbox)
    for bbox in bbox_list:
        recursive_divide_bbox(markers_on_map_url+bbox)
    
def write_to_geojson_file(country,all_data):
    feature_collection = FeatureCollection(all_data)
    with open(f'{country}.geojson', "w", encoding='utf8') as f:
        dump(feature_collection, f, ensure_ascii=False) 
    
def fetch_hotel(url):
    try:
        response = requests.get(url, headers=headers)
        # Extracting the Text:
        text = response.text
        hotel = BeautifulSoup(text, 'html.parser')
        return hotel
    except Exception as e:
        logger.info(str(e), 'fetch_hotel')

def parsing_hotel_data(url):
    try:
        hotel = fetch_hotel(url)
        hotel_data = HotelData(hotel)
        hotel_coordinates = hotel_data.get_hotel_coordinates(hotel)
        point = Point(hotel_coordinates)
        feature = Feature(geometry=point, properties=hotel_data.properties)
        extract_hotel_images(hotel_data, hotel)
        return feature
    except Exception as e:
        logger.info(str(e), 'parsing_hotel_data')
    
def extract_hotel_images(hotel_data, hotel):
    image_urls = hotel_data.get_hotel_images_url(hotel)
    hotel_name = hotel_data.get_hotel_name(hotel).replace(' ', '_')
    path = f'./hotels_images/{hotel_name}/'
    if not os.path.exists(path):
        os.makedirs(path, mode=0o777)
    download_images(path, image_urls)

def download_images(path, image_urls):
    for url in image_urls:
        image_name = url.split('/')[-1].split('?')[0]
        path_image = path + image_name
        response = requests.get(url)
        if response.status_code == 200:
            with open(path_image,'wb') as file:
                file.write(response.content)
                    

if __name__ == '__main__':
    start_time = time()
    logger.info(f"start downloading hotels")
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.submit(recursive_divide_bbox(
            markers_on_map_url+'34.2654333839,29.4533796,35.8363969256,33.3356317'))
    logger.info('start scraping %s hotels', len(hotels_urls))
    all_data = []
    with ProcessPoolExecutor(max_workers=16) as executor:
        all_data = list(executor.map(parsing_hotel_data, hotels_urls))
    logger.info('start writing to geojson file')
    with ThreadPoolExecutor() as executor:
        executor.submit(write_to_geojson_file('israel', all_data))
    end_time = time()
    total_time = (end_time - start_time)/ 60
    logger.info('finish all in: %s sec', total_time)
