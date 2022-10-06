from booking_test import WebScraper
import pycountry
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(_name_)


def get_country_name():
    while True:
        try:
            country = input('please enter country name:')
            if(pycountry.countries.get(name=country)):
                return country
        except Exception as e:
            print("please enter a valid country")


if __name__ == '__main__':
    country = get_country_name()
    iso_code = pycountry.countries.get(name=country).alpha_2
    start_time = time.time()
    logger.info(f"start scraping: {start_time}")
    webScraper = WebScraper(country, iso_code)
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"finish all in: {total_time}")
