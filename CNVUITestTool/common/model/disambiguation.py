from common.model.combo_component import ComboComponent


class Disambiguation(dict):

    def __init__(self, name):
        super().__init__()
        self.__dict__ = self
        self.name = name
        self.current_options = []

    def parse_disambiguation(self, disambiguation_element):
        disambiguation_options = disambiguation_element.find_elements_by_xpath('.//*[@class="current-option-type"]')
        for disambiguation_option in disambiguation_options:
            option_values = [item.text for item in disambiguation_option.find_elements_by_xpath('./ul//li//a')]
            self.current_options.append(option_values)
