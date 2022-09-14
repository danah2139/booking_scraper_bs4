from booking_scraper import WebScraper
import pycountry


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
    webScraper = WebScraper(country, iso_code)
