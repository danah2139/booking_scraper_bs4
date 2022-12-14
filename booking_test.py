from concurrent.futures import ThreadPoolExecutor
import requests
import aiofiles
import os
import time
from bs4 import BeautifulSoup
from geojson import Feature, Point, FeatureCollection, dump
import geopandas as gpd
from hotel_data import HotelData


def devide_bbox(bbox):
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


class WebScraper():
    base_url = 'https://www.booking.com'
    markers_on_map_url = base_url + '/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEJuAEZyAEM2AED6AEB-AECiAIBqAIDuALJ3LyYBsACAdICJGY0ZmExYzc2LTlmOGMtNGM0OC04YTA1LTkzYzc3NDdjZmEwY9gCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=311644e806e807a6&aid=304142&dest_type=country&sr_id=&ref=searchresults&limit=100&stype=1&lang=en-gb&ssm=1&sech=1&ngp=1&room1=A%2CA&maps_opened=1&esf=1&sr_lat=&sr_long=&dba=1&dbc=1&srh=191867%2C3016146%2C301272%2C6948254%2C51288%2C343954%2C301050%2C6478778%2C2337735%2C1357296%2C338044%2C451028%2C5390634%2C1420234%2C4373824%2C173909%2C1865108%2C238601%2C54257%2C542266%2C180434%2C361801%2C1105263%2C4246076%2C270718&somp=1&mdimb=1%20&tp=1%20&img_size=270x200%20&avl=1%20&nor=1%20&spc=1%20&rmd=1%20&slpnd=1%20&sbr=1&at=1%20&sat=1%20&ssu=1&srocc=1&nflt=ht_id%3D204;BBOX='
    country_df = gpd.read_file("zip://TM_WORLD_BORDERS-0.3.zip")
    headers = {
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/83.0.4103.116 Safari/537.36'}

    def __init__(self, country, iso_code):
        self.country = country
        self.iso_code = iso_code
        self.hotels_urls = set()
        # Global Place To Store The Data:
        self.all_data = []
        self.all_links = []
        self.main()


    def fetch_hotel(self, url):
        try:
            response  = requests.get(url,headers= self.headers)
            # Extracting the Text:
            text = response.text()
            hotel = BeautifulSoup(text, 'html.parser')
            # Extracting hotel:
            hotel_data = HotelData(hotel)
            feature = self.parsing_hotel_data(hotel_data, hotel)
            # self.extract_hotel_images(hotel_data, hotel)
            return feature
        except Exception as e:
            print(str(e), 'fetch_hotel')
            return

    def extract_hotel_images(self, hotel_data, hotel):
        image_urls = hotel_data.get_hotel_images_url(hotel)
        hotel_name = hotel_data.get_hotel_name(hotel).replace(' ', '_')
        # currentDir = os.path.abspath(os.path.dirname(__file__))
        path = f'./hotels_images/{hotel_name}/'
        if not os.path.exists(path):
            os.makedirs(path, mode=0o777)
        # path = os.path.join(currentDir, path)
        # self.download_images(path, image_urls)

    def fetch_map(self, url):
            response= requests.get(url,headers= self.headers)
            json_response = response.json()
            hotels = json_response['b_hotels']
            if(len(hotels) <= 1):
                return
            self.add_hotels_url_to_set(hotels)
            bbox = url.split('BBOX=')[1]
            bbox_list = devide_bbox(bbox)
            for bbox in bbox_list:
                self.fetch_map(self.markers_on_map_url+bbox)

    def add_hotels_url_to_set(self, hotels):
        for hotel in hotels:
            link_hotel = hotel['b_url'].split(';')[0]
            if(link_hotel and link_hotel.split('hotel/')[1][0:2] == self.iso_code.lower()):
                hotel_url = self.base_url + link_hotel
                hotel_url = hotel_url.split('?')[0]
                self.hotels_urls.add(hotel_url)
                print(
                    f'hotel number:{len(self.hotels_urls)} ,hotel url: {hotel_url}, time:{time.ctime()}')
                # print(self.hotels_urls, 'self.hotels_urls')

    # async def download_images(self, session, path, image_urls):
    #     for url in image_urls:
    #         image_name = url.split('/')[-1].split('?')[0]
    #         path_image = path + image_name
    #         async with session.get(url) as resp:
    #             if resp.status == 200:
    #                 f = aiofiles.open(path_image, mode='wb')
    #                 f.write(await resp.read())
    #                 f.close()

    async def parsing_hotel_data(self, hotel_data, hotel):
        try:
            hotel_coordinates = hotel_data.get_hotel_coordinates(hotel)
            point = Point(hotel_coordinates)
            feature = Feature(geometry=point, properties=hotel_data.properties)
            return feature
        except Exception as e:
            print(str(e), 'parsing_hotel_data')

    def start_requests(self):
        country_bbox = self.country_df[self.country_df["NAME"].str.lower(
        ) == self.country.lower()].geometry.values[0].bounds
        country_bbox = str(country_bbox)[1:-1].replace(' ', '')
        [min_lon, min_lat, max_lon, max_lat] = country_bbox.split(',')
        min_lon = float(min_lon) - 0.5
        min_lat = float(min_lat) - 0.5
        max_lon = float(max_lon) + 0.5
        max_lat = float(max_lat) + 0.5
        country_bbox = f'{min_lon},{min_lat},{max_lon},{max_lat}'
        return self.markers_on_map_url + country_bbox

    def main(self):
        country_markers_on_map_url = self.start_requests()
        print(f"start recursive: {time.ctime()}")
        with ThreadPoolExecutor() as executor:
            executor.submit(self.fetch_map(country_markers_on_map_url))

        print(f"start parsing hotels: {time.ctime()}")
        with ThreadPoolExecutor() as executor:
            executor.map(self.fetch_hotel, self.hotels_urls)
            # Storing the raw HTML data.
        feature_collection = FeatureCollection(self.all_data)
        with open(f'{self.country}.geojson', "w", encoding='utf8') as f:
            dump(feature_collection, f, ensure_ascii=False)
