import aiohttp
import asyncio
import aiofiles
import os
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

    def __init__(self, country, iso_code):
        self.country = country
        self.iso_code = iso_code
        self.hotels_urls = []
        # Global Place To Store The Data:
        self.all_data = []
        self.all_links = []
        # self.master_dict = {}
        self.count_hotels = 0
        # Run The Scraper:
        asyncio.run(self.main())

    async def fetch_hotel(self, session, url):
        try:
            async with session.get(url) as response:
                # Extracting the Text:
                text = await response.text()
                hotel = BeautifulSoup(text, 'html.parser')
                # Extracting hotel:
                hotel_data = HotelData(hotel)
                feature = await self.parsing_hotel_data(hotel_data, hotel)
                await self.extract_hotel_images(hotel_data, hotel, session)
                return feature
        except Exception as e:
            print(str(e))

    async def extract_hotel_images(self, hotel_data, hotel, session):
        image_urls = hotel_data.get_hotel_images_url(hotel)
        hotel_name = hotel_data.get_hotel_name(hotel).replace(' ', '_')
        # currentDir = os.path.abspath(os.path.dirname(__file__))
        path = f'./hotels_images/{hotel_name}/'
        if not os.path.exists(path):
            os.makedirs(path, mode=0o777)
        # path = os.path.join(currentDir, path)
        await self.download_images(session, path, image_urls)

    async def fetch_map(self, session, url):
        async with session.get(url) as response:
            json_response = await response.json()
            hotels = json_response['b_hotels']
            if(len(hotels) > 1):
                bbox = url.split('BBOX=')[1]
                bbox_list = devide_bbox(bbox)
                for bbox in bbox_list:
                    self.all_links.append(self.markers_on_map_url+bbox)
            for hotel in hotels:
                link_hotel = hotel['b_url'].split(';')[0]
                if(link_hotel.split('hotel/')[1][0:2] != self.iso_code.lower()):
                    continue
                hotel_url = self.base_url + link_hotel
                self.hotels_urls.append(hotel_url)

    async def download_images(self, session, path, image_urls):
        for url in image_urls:
            image_name = url.split('/')[-1].split('?')[0]
            path_image = path + image_name
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path_image, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

    async def parsing_hotel_data(self, hotel_data, hotel):
        try:
            self.count_hotels += 1
            # hotel_url = hotel.url.split('?')[0]
            # print('hotel number:%s ,hotel url: %s',
            #     self.count_hotels, hotel_url)
            hotel_coordinates = hotel_data.get_hotel_coordinates(hotel)
            point = Point(hotel_coordinates)
            feature = Feature(geometry=point, properties=hotel_data.properties)
            return feature
        except Exception as e:
            print(str(e))

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
        self.all_links.append(self.markers_on_map_url + country_bbox)

    async def main(self):
        hotels_tasks = []
        map_tasks = []

        headers = {
            "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}

        self.start_requests()
        async with aiohttp.ClientSession(headers=headers) as session:
            for url in self.all_links:
                map_tasks.append(self.fetch_map(session, url))

            hotels_urls = await asyncio.gather(*map_tasks)
            self.hotels_urls.extend(hotels_urls)

        async with aiohttp.ClientSession(headers=headers) as session:
            for url in self.hotels_urls:
                hotels_tasks.append(self.fetch_hotel(session, url))

            features = await asyncio.gather(*hotels_tasks)
            self.all_data.extend(features)

            # Storing the raw HTML data.
            feature_collection = FeatureCollection(features)
            with open(f'{self.country}.geojson', "w", encoding='utf8') as f:
                dump(feature_collection, f, ensure_ascii=False)
