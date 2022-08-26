from selenium.common.exceptions import NoSuchElementException


class Dish(dict):
    def __init__(self):
        super().__init__()
        self.__dict__ = self
        self.type = 'dish'
        self.id = ''
        self.current_options = {}
        self.selected_keywords = []
        self.upcoming_keywords = []

    def parse(self, dish_item):
        if dish_item.find_element_by_xpath('./div').get_attribute('class') == "dish":
            dish_item = dish_item.find_element_by_xpath('./div')
            self.parse_dish(dish_item)
        elif dish_item.get_attribute('class') == "current-options":
            # item_dict = self._find_item_dict(dish_item)
            options = dish_item.find_elements_by_xpath('./div[@class="current-option-type"]')
            self.parse_current_options(options)

    # def _find_item_dict(self, order_item):
    #     id = self._find_preciding_dish_id(order_item)
    #     for item in self.items:
    #         if item['id'] == id:
    #             return item
    #
    # def _find_preciding_dish_id(self, order_item):
    #     try:
    #         preceding_items = order_item.find_elements_by_xpath('./preceding-sibling::dish-list/div')
    #         if preceding_items:
    #             preceding_item = preceding_items[len(preceding_items) - 1]
    #             return preceding_item.get_attribute('id')
    #     except NoSuchElementException:
    #         return ""

    def parse_dish(self, dish):
        self.id = dish.get_attribute('id')
        parts = dish.find_elements_by_xpath('./*')
        for part in parts:
            if part.get_attribute('class') == 'dish-status markedForCheckOut':
                self.selected_keywords.append('/')
            elif part.get_attribute('class') == 'dish-status checkedOut':
                self.selected_keywords.append('/')
            elif part.get_attribute('class') == 'dish-status markedForAddition':
                self.selected_keywords.append('+')
            elif part.get_attribute('class') == 'dish-status markedForDeletion':
                self.selected_keywords.append('-')
            elif part.get_attribute('class') == 'dish-items-list':
                keywords = part.find_elements_by_xpath('./*')
                for keyword in keywords:
                    if keyword.get_attribute('class') == 'options-available':
                        self.upcoming_keywords.append(keyword.text)
                    elif keyword.text != "":
                        self.selected_keywords.append(keyword.text)

    # def _parse_disambiguation(self, response):
    #     """
    #     Parsing disambiguation options which is different than current options
    #     """
    #     options = self.driver.find_elements_by_xpath(
    #         '//app-order-items/div[@id="assist-order-items-container"]/disambiguation-list//div[@class="current-options disambiguation-options"]/div[@class="current-option-type"]')
    #     if options:
    #         self._parse_current_options(options)


    def parse_current_options(self,options):
        option_key_name=''
        if options.find_elements_by_xpath('./p'):
            option_key_name = options.find_element_by_xpath('./p').text
        option_values = [item.text for item in options.find_elements_by_xpath('./ul//li//a')]
        self.current_options[option_key_name] = option_values

