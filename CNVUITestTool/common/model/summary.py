from selenium.common.exceptions import NoSuchElementException


class Summary:
    def __init__(self,driver):
        self._driver = driver


    def _parse_order_summary(self, response):
        try:
            elm_tax_price = self._driver.find_element_by_xpath(
                '//a[@class="order-price tax-amount"]/span[@class="price"]')
            response.summary['tax'] = elm_tax_price.text

            elm_total_amount = self._driver.find_element_by_xpath(
                '//a[@class="order-price total-amount"]/span[@class="price"]')
            response.summary['total'] = elm_total_amount.text

            summary_items = self._driver.find_elements_by_xpath('//div[@class="order-item-detail"]')

            for summary_item in summary_items:
                summary_dict = self._get_empty_summary_dict()
                self._parse_order_summary_item(summary_item, summary_dict)
                response.summary['items'].append(summary_dict)
        except NoSuchElementException:
            pass

    def _parse_order_summary_item(self, summary_item, summary_dict):
        qty = summary_item.find_element_by_xpath('./span/span[@class="order-item-qty"]/span[@class="qty"]').text
        price = summary_item.find_element_by_xpath('./span/span[@class="order-item-qty"]').text.replace(qty,
                                                                                                        '').strip()

        name = summary_item.find_element_by_xpath('./span[@class="order-item-name"]').text.replace(qty, '').replace(
            price, '').strip()

        summary_dict['qty'] = qty
        summary_dict['price'] = price
        summary_dict['name'] = name

        customizations = summary_item.find_elements_by_xpath('./ul//li')
        for customization in customizations:
            cust_key = customization.find_element_by_xpath('./span[@class="customization-name"]').text
            cust_values = customization.text.replace(cust_key, '').strip()
            summary_dict['customizations'][cust_key] = cust_values

    def _get_empty_summary_dict(self):
        return {
            'id': '',
            'name': '',
            'price': '',
            'qty': '',
            'customizations': {}
        }
