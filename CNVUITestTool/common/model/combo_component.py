from common.model.dish import Dish


class ComboComponent(dict):
    def __init__(self,name):
        super().__init__()
        self.__dict__ = self
        self.name = name
        self.dishes = []

    def add_dish(self,dish):
        self.dishes.append(dish)



