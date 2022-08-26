from common.model.combo_component import ComboComponent
from common.model.disambiguation import Disambiguation
from common.model.dish import Dish


class Combo(dict):
    """Class to contain response syntax for response against a cart state"""

    def __init__(self, name):
        super().__init__()
        self.__dict__ = self
        self.type = 'combo'
        self.name = name
        self.combo_components = []
        self.disambiguations = []

    def parse(self, combo_element):
        disambiguation_elements = combo_element.find_elements_by_xpath(
            './/*[@class="current-options disambiguation-options" or @class="associated-combo-category"]')
        current_disambiguation = None
        for disambiguation_element in disambiguation_elements:
            if disambiguation_element.get_attribute('class') == "associated-combo-category":
                name = disambiguation_element.text
                current_disambiguation = Disambiguation(name)
            if disambiguation_element.get_attribute('class') == "current-options disambiguation-options":
                current_disambiguation.parse_disambiguation(disambiguation_element)
                self.disambiguations.append(current_disambiguation)
        self.parse_components(combo_element)

    def parse_components(self, options):
        """
        Parsing disambiguation options which is different than current options

        """
        components = options.find_elements_by_xpath(
            './/*[@class="dish-container"]//*[@class="associated-combo-category" or @class="dish" or @class="current-options"]')
        current_component = None
        current_dish = None
        for component in components:
            if component.get_attribute('class') == "associated-combo-category":
                name = component.text
                current_component = ComboComponent(name)
            if component.get_attribute('class') == "dish":
                current_dish = Dish()
                current_dish.parse_dish(component)
                current_component.add_dish(current_dish)
                self.combo_components.append(current_component)
            if component.get_attribute('class') == "current-options":
                current_dish.parse_current_options(component.find_element_by_xpath('.//*[@class="current-option-type"]'))