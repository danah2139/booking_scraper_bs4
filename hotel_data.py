from utils import logging

logger = logging.getLogger(__name__)

class HotelData:
    def __init__(self, hotel):
        self.properties = {}
        self.push_hotel_data_to_properties(hotel)

    def get_hotel_coordinates(self, hotel):
        coordinates = hotel.select_one(
            'script:-soup-contains("defaultCoordinates")')
        coordinates = str(coordinates).split('defaultCoordinates: [')[1]
        coordinates = coordinates.split('],')[0].replace("'", '').split(',')
        x = coordinates[0].strip()
        y = coordinates[1].strip()
        return (float(y), float(x))

    def get_hotel_name(self, hotel):
        hotel_name = hotel.select_one("#hp_hotel_name_reviews")
        hotel_name = hotel_name.text.replace('\n', '') if hotel_name else 'None'
        return hotel_name

    def get_hotel_address(self, hotel):
        try:
            hotel_address = hotel.select_one(
                '#showMap2 .hp_address_subtitle')
            hotel_address = hotel_address.text.replace(
                '\n', '')
        except Exception as e:
            logger.info(str(e) ,'get_hotel_address')
            hotel_address = 'None' 
        return hotel_address

    def get_hotel_description(self, hotel):
        hotel_descrption = hotel.select(
            '#property_description_content p')
        text = ''
        for row in hotel_descrption:
            if(row):
                text += row.get_text()
        return text

    def get_hotel_rate(self, hotel):
        hotel_rate = hotel.select_one(
            '[data-testid="review-score-component"] div')
        return hotel_rate.text if hotel_rate else None

    def get_hotel_number_of_stars(self, hotel):
        number_of_stars = len(
            hotel.select('[data-testid = "quality-rating"] span'))
        return number_of_stars

    def get_hotel_events(self, hotel):
        events = {}
        events_near_hotel = hotel.select(
            '.property_page_surroundings_block')
        print(events_near_hotel, 'events_near_hotel')
        for event in events_near_hotel:
            event_key = event.select_one(
                '.bui-list__description').text
            event_value = event.select_one(
                '.hp_location_block__section_list_distance').text
            events[event_key] = event_value
        return events

    def get_hotel_services(self, hotel):
        hotel_services = hotel.select('.hotel-facilities-group')
        services = {}
        for service in hotel_services:
            service_key = service.select_one(
                '.hotel-facilities-group__title-text')
            service_key = service_key.text.replace(
                '\n', '') if service_key else 'None'
            service_value = service.select_one(
                '.hotel-facilities-group__policy')
            if(service_value):
                services[service_key] = service_value.text.replace('\n', '')
            else:
                services[service_key] = []
                service_items = service.select(
                    '.hotel-facilities-group__list-item')
                for item in service_items:
                    item_value = item.select_one(
                        '.bui-list__body .bui-list__description')
                    item_value = item_value.text.replace(
                        '\n', '') if item_value else 'None'
                    services[service_key].append(item_value)
        return services

    def get_hotel_comments(self, hotel):
        hotel_comments = hotel.select(
            '[data-testid="featuredreview-text"] div')      
        first_comment = hotel_comments[0].text if len(
            hotel_comments) > 0 else 'None'
        second_comment = hotel_comments[1].text if len(
            hotel_comments) > 1 else 'None'
        return f'first_comment:{first_comment}. second_comment: {second_comment}'

    def get_hotel_images_url(self, hotel):
        image_urls = hotel.select('.active-image img')
        image_urls = [image_url["src"] for image_url in image_urls]
        return image_urls

    def push_hotel_data_to_properties(self, hotel):
        self.properties['hotel_name'] = self.get_hotel_name(hotel)
        self.properties['hotel_address'] = self.get_hotel_address(hotel)
        self.properties['hotel_descrption'] = self.get_hotel_description(hotel)
        self.properties['hotel_rate'] = self.get_hotel_rate(hotel)
        self.properties['number_of_stars'] = self.get_hotel_number_of_stars(
            hotel)
        # self.properties['events_near_hotel'] = self.get_hotel_events(hotel)
        self.properties['hotel_services'] = self.get_hotel_services(hotel)
        self.properties['hotel_comments'] = self.get_hotel_comments(hotel)
