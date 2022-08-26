from common.model.combo import Combo
from common.model.disambiguation import Disambiguation
from common.model.dish import Dish

class SeleniumResponse(dict):
    """Class to contain response syntax for response against a cart state"""

    def __init__(self):
        super().__init__()
        self.__dict__ = self
        self.utterance = None
        self.dishes = []
        self.disambiguations = []


    # def __eq__(self, other):
    #     if not isinstance(other, SeleniumResponse):
    #         return False
    #     return self.items == other.items and self.summary == other.summary

    # def to_dict(self):
    #     """Instance serialization"""
    #     return self.__dict__

    def parse(self,driver):
        dish_items = self._get_dish_items(driver)
        if dish_items is not None:
            self._parse_order_items(dish_items)

        combo_items = self._get_combos(driver)
        if combo_items is not None:
            self._parse_combo_items(combo_items)

    def _parse_order_items(self, dish_items):
        current_dish = None
        for dish in dish_items:
            if dish.find_elements_by_xpath('./div[@class="dish"]'):
                current_dish = Dish()
                current_dish.parse_dish(dish.find_element_by_xpath('./div'))
                self.dishes.append(current_dish)
            if dish.get_attribute('class') == "current-options":
                current_dish.parse_current_options(dish.find_element_by_xpath('./*'))
            if dish.find_elements_by_xpath('./div[@class="dish disambiguation"]'):
                disambiguation = Disambiguation(None)
                disambiguation.parse_disambiguation(dish.find_element_by_xpath('.//div[@class="current-options disambiguation-options"]'))
                self.disambiguations.append(disambiguation)

    def _parse_combo_items(self, combo_items):
        for combo_item in combo_items:
            name = combo_item.find_element_by_xpath('//*[@class="associated-combo"]').text
            combo = Combo(name)
            combo.parse(combo_item)
            self.dishes.append(combo)

    def _get_dish_items(self,driver):
        return driver.find_elements_by_xpath(
            '//app-order-items/div[@id="assist-order-items-container"]/*[not(@class="dish-coupon-container")]')

    def _get_combos(self,driver):
        return driver.find_elements_by_xpath(
            '//app-order-items/div[@id="assist-order-items-container"]/*[@class="dish-coupon-container"]')