import contextlib
import time
import logging
import ast
import json
import threading


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException,InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager
from re import split

from api.service import Task
from common.settings import worker_pool as pool
from common.settings import email, password, drivethru_url,eapos_url,drivethru_operator_url,blakes_url

# LOGGER.setLevel(logging.WARNING)
from common.model.selenium_response import SeleniumResponse

STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"







class BrowserWorker:
    """
    Contains worker logic for BrowserTask. Uses selenium driver to parse
    different parts of the UI and sends response

    Attributes
    ----------

    Methods
    -------
    get_instance()
        Return a new instance or existing singlenton instance of class
    is_locked()
        Method to check if there is another task running by this worker.
    execute(dict, obj<response>)
        Run the execute workflow. Based on action type (`init`, `close`,
        `menu` etc) it calls appropriate private method.
    """

    # __instance = None

    _lock = False

    # _init_url_blakes = blakes_url
    # _init_url_drivethru = drivethru_url
    # _init_url_drivethru_operator = drivethru_operator_url
    _is_initialized = False

    def __init__(self):
        """Singleton class"""
        # if BrowserWorker.__instance is None:
        #     BrowserWorker.__instance = self
        self._stop_event = threading.Event()
        self._previous_response = None
        self._session_id = None

    # public methods ..........................................................

    @staticmethod
    def get_instance(session_id):
        """Returns a new instance or Singleton instance of class"""
        try:
            worker = pool[session_id]
        except KeyError:
            worker = BrowserWorker()
            pool[session_id] = worker
        return worker

    def is_locked(self):
        """Check if worker is in execution or not"""
        return self._lock

    def execute(self, params, response):
        getattr(self, "_%s_action" % params['action'])(params, response)

    # private actions methods .................................................

    def _init_action(self, params, response):
        """
        Logic for `init` action.
        """
        self._driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        data = ast.literal_eval(params['data'])
        type = data['type']
        restaurant = data['restaurant'].lower()
        _init_url = "https://%s.staging.v2.conversenow.ai" % restaurant
        operator ='/operator'
        employee ='/employee'

        if type == 'DT':
            data = ast.literal_eval(params['data'])
            mac_id = data['mac_id']
            mac_id = mac_id.strip()
            tracker_id = data['tracker_id']
            tracker_id = tracker_id.strip()
            if tracker_id is None:
                url = _init_url + employee + '/' + mac_id
                self._driver.get(url)
                self._handle_login(params)
                self._wait_for_customer_to_dial_in()
            elif tracker_id is not None:
                url = _init_url + employee + '/' + mac_id + '/' + tracker_id
                self._driver.get(url)
                self._handle_login(params)
                self._wait_for_menu_to_load()

        if type == 'OA':
            data = ast.literal_eval(params['data'])

            tracker_id = data['tracker_id']
            tracker_id = tracker_id.strip()
            if len(tracker_id) == 0:
                url = _init_url + operator + '/'
                self._driver.get(url)
                self._handle_login(params)
                self._extention_details(params)
                self._wait_for_customer_to_dial_in()
            elif len(tracker_id) > 0:
                url = _init_url + operator + '/' + tracker_id
                self._driver.get(url)
                self._handle_login(params)
                self._wait_for_menu_to_load()

        logging.debug("Starting watch loop")
        # Clear if any stop event is set
        self._stop_event.clear()
        t = threading.Thread(target=self._run_watch_loop, args=(response,), name='watcher', daemon=True)
        # t = threading.Timer(1, self._run_watch_loop, args=(response,))
        t.start()

    def _lane_action(self,params):
        logging.info(params)
        xpath = '//*[@class="car-available"]'
        self._driver.find_element_by_xpath(xpath).click()

    def _menu_action(self, params, response):
        logging.info(params)
        elm_menu = self._driver.find_element_by_id('menu')

        # item = params['data']['']
        # item = 'bread'
        data = ast.literal_eval(params['data'])
        item_name = data['name']
        item_name = item_name.strip()
        # item_name = ' '.join(a.capitalize() for a in split('([^a-zA-Z0-9])', item_name) if a.isalnum())
        # xpath = './ul/li/a/span[text()="%s"]/../..|./ul/li/a/span[text()="%s"]/../..'%(item_name.lower(),item_name)
        xpath = '//*[@name="catalogItem"]/..//*[@class="menu-category-list"]/span/../..'
        elm_menu_btn = elm_menu.find_elements_by_xpath(xpath)
        try:
            for items in elm_menu_btn:
                if items.text.lower() == item_name.lower():
                    items.click()
                    self.wait_for_page_load()
        except NoSuchElementException:
            print("Element not found")
        # elm_sub_items = self._driver.find_element_by_class_name('menu-category-items')
        # sub_items = elm_sub_items.find_elements_by_xpath('./ul/li[@class="category-item"]')
        # response.data['sub_items'] = [item.text for item in sub_items]

    def _submenu_action(self, params, response):
        response.data = ""

        logging.info(params)
        data = ast.literal_eval(params['data'])
        item_name = data['name']
        #callerNumberitem_name = ' '.join(a.capitalize() for a in split('([^a-zA-Z0-9])', item_name) if a.isalnum())
        WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'menu-category-items')))
        # xpath = '//a[@class="menu-category-list"]//span[text()="%s"]' % item_name.strip()
        xpath = '//*[@class="category-item"]//*[@class="menu-category-list"]/span |//*[contains(@class,"category-item")]//*[@class="menu-category-list"]//span[@class="coupon-code"]'
        elm_submenu_item = self._driver.find_elements_by_xpath(xpath)
        try:
            for element in elm_submenu_item:
                if element.text.lower() == item_name.lower():
                    element.click()
        except NoSuchElementException:
            print("Element not found")
            response.message = 'No Such element found'
        self._wait_action()
        self.wait_for_page_load()
        time.sleep(2)
        xpath = '//*[@class="close-btn"]'
        elm_close = self._driver.find_element_by_xpath(xpath)
        elm_close.click()

    def _couponcode_action(self, params, response):
        logging.info(params)
        data = ast.literal_eval(params['data'])
        code = data['code']
        code = code.strip()
        coupon_code = self._driver.find_element_by_xpath('//input[@formcontrolname="coupon_code"]')
        coupon_code.click()
        coupon_code.send_keys(code)
        self._driver.find_element_by_xpath('//*[@class="update-btn" and text()="Apply Coupon"]').click()

    def _recommendation_action(self, params, response):
        logging.info(params)
        data = ast.literal_eval(params['data'])
        item = data['item']
        item = item.strip()
        items = self._driver.find_elements_by_xpath('//*[@class="recommended-item"]')
        for each_item in items:
            each_val =''.join(e for e in each_item.text.lower() if e.isalnum())
            item=''.join(e for e in item.text.lower() if e.isalnum())
            if each_val.strip() == item.strip():
                each_item.click()

    def _add_to_summary_action(self, params, response):
        response.data = ""
        logging.info(params)
        data = ast.literal_eval(params['data'])
        id = data['id']
        id = id.strip()
        xpath = '//app-order-items//div[@id="%s"]//div[contains(@class, "dish-status")]' % id
        elm_order_status = self._driver.find_element_by_xpath(xpath)
        elm_order_status.click()

    def _customize_action(self, params, response):
        response.data = ""
        logging.info(params)
        logging.debug("customize option")
        data = ast.literal_eval(params['data'])
        item_id = data['id']
        customization_type = data['customization_type']
        customization_type = customization_type.strip()
        customization_name = data['customization_name']
        # customization_name = ' '.join(a.capitalize() for a in split('([^a-zA-Z0-9])', customization_name) if a.isalnum())
        # xpath = '//*[@id="%s"]/following-sibling::div[1]//*[text()="%s"]/..//*[text()="%s"]/..//input' % (item_id, customization_type.lower(), customization_name)
        xpath_cust = '//*[@id="%s"]/../following-sibling::div[1]//*[@class="option-name"]' % item_id
        elm_cust = self._driver.find_elements_by_xpath(xpath_cust)
        try:
            for cust in elm_cust:
                customize = ''.join(e for e in cust.text.lower() if e.isalnum())
                if ''.join(e for e in customization_type.lower() if e.isalnum()) in customize:
                    # xpath = '//*[@id="%s"]/../following-sibling::div[1]//*[text()="%s"]/..//*[@class="option-items"]' % (
                    # item_id, cust.text.lower)
                    elm_item = cust.find_elements_by_xpath('.//..//*[@class="option-items"]')
                    for items in elm_item:
                        if ''.join(e for e in items.text.lower() if e.isalnum()) in ''.join(e for e in customization_name.lower() if e.isalnum()):
                            # xpath = '//*[@id="%s"]/../following-sibling::div[1]//*[text()="%s"]/..//*[text()="%s"]/..//input' % (
                            # item_id, cust.text, items.text)
                            element = items.find_element_by_xpath('.//..//input')
                            element.click()
                            self.wait_for_page_load()
                            self.page_has_loaded()
                            break

        except NoSuchElementException:
            print("Element not found")
            response.message = 'No Such element found'

    def _disambiguation_action(self, params, response):
        logging.info(params)
        logging.debug("customize option")
        data = ast.literal_eval(params['data'])
        disambiguation_type = data['disambiguation_type'].strip()
        name = data['name'].strip()

        try:

            if len(disambiguation_type)>0:
                xpath_cust = '//*[@class="dish disambiguation"]//*[@class="option-name"]'
                elm_cust = self._driver.find_elements_by_xpath(xpath_cust)
                for element in elm_cust:
                    if element.text.lower() == disambiguation_type.lower():
                        items = '//*[@class="dish disambiguation"]//*[text()="%s"]/..//*[@class="option-items"]' % element.text
                        elem_items = self._driver.find_elements_by_xpath(items)
                        for item in elem_items:
                            if item.text.lower() == name.lower():
                                value = '//*[@class="dish disambiguation"]//*[text()="%s"]/..//*[text()="%s"]/..//input' % (
                                element.text, item.text)
                                self._driver.find_element_by_xpath(value).click()
                                self.wait_for_page_load()
                                break
            elif len(disambiguation_type)==0:
                options= self._driver.find_elements_by_xpath('//*[@class="current-options"]//*[@class="option-items"]')
                for option in options:
                    customize = ''.join(e for e in option.text.lower() if e.isalnum())
                    if ''.join(e for e in name.lower() if e.isalnum()) in customize:
                        option.find_element_by_xpath('.//../input').click()
                        break


        except:
            print("No Such element found")
            response.message = 'No Such element found'

    def _edit_action(self, params, response):
        response.data = ""
        logging.info(params)
        logging.debug("edit option")
        data = ast.literal_eval(params['data'])
        item_id = data['id']
        customization_type = data['customization_type']
        customization_type = customization_type.strip()
        customization_name = data['customization_name']
        items_options = customization_name.split('&')
       # xpath = '//*[@id="%s"]//*[@class="dish-item selected-option %s"] | //*[@id="%s"]//*[@class="options-available"]//*[text()="%s"]
        xpath = '//*[@id="%s"]//*[contains(@class,"dish-item") and contains(@data-target,"#popoverModal")]' % (item_id)
        elm_cust = self._driver.find_elements_by_xpath(xpath)
        for each_type in elm_cust:
            class_name = each_type.get_attribute("class")
            class_name = ''.join(e for e in class_name if e.isalnum())
            if ''.join(e for e in customization_type.lower() if e.isalnum()) in (class_name.lower()):
                each_type.click()
                break
            if ''.join(e for e in customization_type.lower() if e.isalnum()) in ''.join(e for e in each_type.text.lower() if e.isalnum()):
                each_type = each_type.find_element_by_xpath('.//..')
                self._driver.refresh()
                each_type.click()
                break

        WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@class="item-options"]')))
        for item in items_options:
            xpath ='//*[contains(@class,"list-customization")]//*[@class="option-name" or @class="option-items"]'
            # xpath2='//*[contains(@class,"list-customization")]//*[contains(@class="option-items"]'
            #xpath = '//*[@class="option-name" and text()="%s"]/../..' % item.strip()
            options = self._driver.find_elements_by_xpath(xpath)
            # options2 = self._driver.find_elements_by_xpath(xpath2)
            for option in options:
                #option_val = option.get_attribute('value')
                option_val = ''.join(e for e in option.text.lower() if e.isalnum())
                if option_val == ''.join(e for e in item.lower() if e.isalnum()):
                    # option = option.find_element_by_xpath('./../..//input')
                    option.find_element_by_xpath('./preceding-sibling::input').click()
                    break
            self._wait_action()
            continue


        webdriver.ActionChains(self._driver).send_keys(Keys.TAB).perform()
        webdriver.ActionChains(self._driver).send_keys(Keys.ESCAPE).perform()

    def _customization_available_action(self, params, response):
        response.data = ""
        logging.info(params)
        logging.debug("customization_available")
        data = ast.literal_eval(params['data'])
        item_id = data['id']
        customization_type = data['customization_type']
        customization_type = customization_type.strip()
        customization_name = data['customization_name']
        items_options = customization_name.split('&')
       # xpath = '//*[@id="%s"]//*[@class="dish-item selected-option %s"] | //*[@id="%s"]//*[@class="options-available"]//*[text()="%s"]
        xpath = '//*[@id="%s"]//*[@class="options-available"]' %item_id
        elm_cust = self._driver.find_elements_by_xpath(xpath)
        for each_type in elm_cust:
            class_name=''.join(e for e in each_type.text if e.isalnum())
            if ''.join(e for e in customization_type.lower() if e.isalnum()) in (class_name.lower()):
                each_type.click()
                self.wait_for_page_load()

        WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@class="item-options"]')))
        for item in items_options:
            xpath ='//*[contains(@class,"list-customization")]//*[@class="option-name"]'
            #xpath = '//*[@class="option-name" and text()="%s"]/../..' % item.strip()
            options = self._driver.find_elements_by_xpath(xpath)
            for option in options:
                #option_val = option.get_attribute('value')
                option_val = ''.join(e for e in option.text.lower() if e.isalnum())
                if option_val == ''.join(e for e in item.lower() if e.isalnum()):
                    option=option.find_element_by_xpath('.//../..//input')
                    option.click()
                    self.wait_for_page_load()
        self._wait_action()

        webdriver.ActionChains(self._driver).send_keys(Keys.TAB).perform()
        webdriver.ActionChains(self._driver).send_keys(Keys.ESCAPE).perform()

    def _wait_action(self):
        overlay = len(self._driver.find_elements_by_id('overlay'))
        while overlay != 0:
            overlay = len(self._driver.find_elements_by_id('overlay'))
        time.sleep(1)

    def _takeover_action(self, params, response):
        logging.info(params)
        logging.debug("takeover")
        try:
            elm_takeover = self._driver.find_element_by_xpath('//li[@class="button take-over"]')
            elm_takeover.click()
        except NoSuchElementException:
            msg = "Take over button not visible yet. Waiting for customer."
            logging.error(msg)
            response.message = msg
            response.status = STATUS_FAILED

    def _manualorder_action(self, params, response):
        response.data = ""
        logging.info(params)
        logging.debug("Manual Order")
        data = ast.literal_eval(params['data'])
        store = data['store']
        phno = data['phno']

        xpath = '//*[@class="manual-order-btn btn"]'
        elm_manualorder_btn = self._driver.find_element_by_xpath(xpath)
        elm_manualorder_btn.click()
        WebDriverWait(self._driver, 15).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'manual-order-container')))
        store_name = self._driver.find_element_by_xpath('//input[@formcontrolname ="store_id"]')
        store_name.clear()
        store_name.click()
        store_name.send_keys(store.strip())
        store_name.send_keys(Keys.ENTER)
        elm_phno = self._driver.find_element_by_xpath('//input[@formcontrolname="phone_number"]')
        elm_phno.clear()
        elm_phno.click()
        elm_phno.send_keys(phno.strip())
        xpath = '//*[@class="update-btn btn" and text()="Start Ordering"]'
        elm_startordering_btn = self._driver.find_element_by_xpath(xpath)
        time.sleep(3)
        elm_startordering_btn.click()

    def _updateprice_action(self, params, response):
        logging.info(params)
        logging.debug("update price")
        xpath = '//*[@class="update-price-btn btn"] | //*[@class="push-to-pos"]'
        elm_update_btn = self._driver.find_element_by_xpath(xpath)
        elm_update_btn.click()
        self.wait_for_page_load()
        self._wait_action()
        try:
            WebDriverWait(self._driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')))
            alert = self._driver.find_element_by_xpath('//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')
            response.message = alert.text
        except :
            WebDriverWait(self._driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//a[@class="order-price tax-amount"]/span[@class="price"] |//*[(@class="total") and  contains(text(),"Total")]/span[@class="price"]')))
            elm_tax_price = self._driver.find_element_by_xpath('//a[@class="order-price tax-amount"]/span[@class="price"] |//*[(@class="total") and  contains(text(),"Tax")]/span[@class="price"]')
            response.data['tax'] = elm_tax_price.text
            elm_total_amount = self._driver.find_element_by_xpath('//a[@class="order-price total-amount"]/span[@class="price"] |//*[(@class="total") and  contains(text(),"Total")]/span[@class="price"]')
            response.data['total'] = elm_total_amount.text

    def _paymenttype_action(self, params, response):
        logging.info(params)
        response.data = ""
        logging.debug("payment method")
        data = ast.literal_eval(params['data'])
        mode = data['mode']
        mode = mode.strip()

        elm_payment = self._driver.find_element_by_xpath('//*[@class="order-btn payment btn"]')
        elm_payment.click()
        WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'payment')))

        xpath = '//*[text()="%s"]' % mode.lower()
        elm_update_btn = self._driver.find_element_by_xpath(xpath)
        elm_update_btn.click()
        if mode == 'card':
            cardno = data['cardno']
            cardno = cardno.strip()
            expmonth = data['expmonth'].strip()
            expyear = data['expyear'].strip()
            cvv = data['cvv'].strip()
            postalcode = data['cvv'].strip()
            xpath = '//*[@formcontrolname="card_number"]'
            cardno_input = self._driver.find_element_by_xpath(xpath)
            cardno_input.clear()
            cardno_input.send_keys(cardno)
            expmonth_input = self._driver.find_element_by_xpath('//*[@formcontrolname="expiration_month"]')
            expmonth_input.clear()
            expmonth_input.send_keys(expmonth)
            expyear_input = self._driver.find_element_by_xpath('//*[@formcontrolname="expiration_year"]')
            expyear_input.clear()
            expyear_input.send_keys(expyear)
            cvv_input = self._driver.find_element_by_xpath('//*[@formcontrolname="cvv"]')
            cvv_input.clear()
            cvv_input.send_keys(cvv)
            postal_input = self._driver.find_element_by_xpath('//*[@formcontrolname="postal_code"]')
            postal_input.clear()
            postal_input.send_keys(postalcode)
            self._driver.find_element_by_xpath('//a[@class="update-btn btn" and text()="Save"]').click()
            try:
                WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located(
                    (By.XPATH, '//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')))
                alert = self._driver.find_element_by_xpath(
                    '//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')
                response.message = alert.text
            except:
                response.message = 'credit card details updated successfully'

            # response.data['cardnumber'] = cardno_input.get_attribute('value')
            # response.data['expmonth'] = expmonth_input.get_attribute('value')
            # response.data['expyear'] = expyear_input.get_attribute('value')
            # response.data['cvv'] = cvv.get_attribute('value')
            # response.data['postal'] = postal_input.get_attribute('value')

    def _exitform_action(self, params, response):
        response.data = ""
        logging.info(params)
        logging.debug("Exit Order")
        data = ast.literal_eval(params['data'])
        category = data['category']
        category = ' '.join(a.capitalize() for a in split('([^a-zA-Z0-9])', category) if a.isalnum())
        subcategory = data['subcategory']
        feedback = data['feedback']
        xpath = '//*[@class="feedback-category"]//*[@class="category"]'
        category_val = self._driver.find_elements_by_xpath(xpath)
        for each_category in category_val:
            if each_category.text.lower() == category.lower():
                xpath = '//*[@class="feedback-category"]//*[text()="%s"]/..//input' % each_category.text
                self._driver.find_element_by_xpath(xpath).click()
        subcategory_xpath = '//*[@class="feedback-sub-category"]//label'
        subcategory_val = self._driver.find_elements_by_xpath(subcategory_xpath)
        time.sleep(2)
        for each_subcategory in subcategory_val:
            if each_subcategory.text.lower() == subcategory.lower():
                xpath = '//*[@class="feedback-sub-category"]//label[text()="%s"]/..//input' % each_subcategory.text
                self._driver.find_element_by_xpath(xpath).click()
            else:
                break
        feedback_val = self._driver.find_element_by_xpath('//input[@formcontrolname="feedback"]')
        feedback_val.send_keys(feedback)
        save = self._driver.find_element_by_xpath('//*[text()= "Save"and @class ="update-btn btn"]')
        # self._driver.execute_script("$(arguments[0]).click();", save)
        time.sleep(2)
        save.click()

    def _exitorder_action(self, params, response):
        logging.info(params)
        response.data = ""
        logging.debug("Exit Order")
        elm_exitpos_btn = self._driver.find_element_by_xpath('//*[@class="push-to-pos exit-order"]')
        elm_exitpos_btn.click()

    def _pushorder_action(self, params, response):
        logging.info(params)
        data = ast.literal_eval(params['data'])
        response.data = ""
        logging.debug("push Order")
        confirmation = data['confirmation']
        elm_pushpos_btn = self._driver.find_element_by_class_name('push-to-pos')
        elm_pushpos_btn.click()
        self.wait_for_page_load()
        self._wait_action()
        try:
            xpath = '//*[@class="update-btn btn" and contains(text(),"%s")]' % confirmation
            self._driver.find_element_by_xpath(xpath).click()
        except :
            print('No confirmation pop up')
            elm_total_price = self._driver.find_element_by_xpath('//app-order-placed//*[contains(text(),"Order Total")]/b[1]')
            response.data['Order_total'] = elm_total_price.text
            elm_order_id = self._driver.find_element_by_xpath('//app-order-placed//*[contains(text(),"Order Total")]/b[2]')
            response.data['Order_id'] = elm_order_id.text

    def _remove_item_cart_action(self, params, response):
        response.data = ""
        logging.info(params)
        data = ast.literal_eval(params['data'])
        id = data['id']
        logging.debug("remove item")
        xpath = '//*[@id="%s"]//*[contains(@class,"dish-item trash")]' % id
        elm_addall_btn = self._driver.find_element_by_xpath(xpath)
        elm_addall_btn.click()

    def _addall_action(self, params, response):
        response.data = ""
        logging.debug("Add all")
        elm_addall_btn = self._driver.find_element_by_XPATH('//*[@class="btn-add"]')
        elm_addall_btn.click()

    def _clearorder_action(self, params, response):
        logging.info(params)
        response.data = ""
        logging.debug("claer cart")
        elm_addall_btn = self._driver.find_element_by_xpath('//*[@class="clear-cart btn"]')
        elm_addall_btn.click()

    def _pickupdelivery_action(self, params, response):
        logging.info(params)
        data = ast.literal_eval(params['data'])
        name = data['name']
        mode = data['mode']
        changeservice = data['changeservice'].strip()
        changeservice = changeservice.lower()

        logging.debug("Delivery - pick up Option")
        elm_pickupdelivery = self._driver.find_element_by_xpath('//li[@class="order-option button"]')
        elm_pickupdelivery.click()
        if changeservice == 'yes':
            self._driver.find_element_by_xpath('//*[@class="change-btn btn"]').click()

        if mode == "delivery":
            address1 = data['address1']
            address2 = data['address2']
            postal_code = data['postal_code']
            city = data['city']
            state = data['state']
            self._driver.find_element_by_xpath('//a[@class="operator-btn delivery"]').click()
            WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'delivery-address')))
            elm_name = self._driver.find_element_by_xpath('//input[@formcontrolname="name"]')
            elm_name.clear()
            elm_name.send_keys(name)
            elm_ad1 = self._driver.find_element_by_xpath('//input[@formcontrolname="address_line_1"]')
            elm_ad1.clear()
            elm_ad1.send_keys(address1)
            elm_ad2 = self._driver.find_element_by_xpath('//input[@formcontrolname="address_line_2"]')
            elm_ad2.clear()
            elm_ad2.send_keys(address2)
            elm_postalcode = self._driver.find_element_by_xpath('//input[@formcontrolname="postal_code"]')
            elm_postalcode.clear()
            elm_postalcode.send_keys(postal_code)
            elm_city = self._driver.find_element_by_xpath('//input[@formcontrolname="locality"]')
            # elm_city.clear()
            elm_city.send_keys(city)
            elm_state = self._driver.find_element_by_xpath('//input[@formcontrolname="administrative_area"]')
            # elm_state.clear()
            elm_state.send_keys(state)
            self._driver.find_element_by_xpath('//a[@class="update-btn btn"]').click()
            WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')))
            alert = self._driver.find_element_by_xpath(
                '//*[@class="alert-response warning"]/p |//*[@class="alert-response error"]/p')
            response.data["name"] = elm_name.get_attribute("value")
            response.data["address1"] = elm_ad1.get_attribute("value")
            response.data["address2"] = elm_ad2.get_attribute("value")
            response.data["postalcode"] = elm_postalcode.get_attribute("value")
            response.data["city"] = elm_city.get_attribute("value")
            response.data["state"] = elm_state.get_attribute("value")
            response.message = alert.text
            response.data = json.dumps(response.data)

        if mode == "pickup":
            self._driver.find_element_by_xpath('//a[@class="operator-btn pick-up"]').click()
            WebDriverWait(self._driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'delivery-address')))
            elm_name = self._driver.find_element_by_xpath('//input[@formcontrolname="name"]')
            elm_name.clear()
            elm_name.send_keys(name)
            self._driver.find_element_by_xpath('//a[@class="update-btn btn"]').click()

        else:
            logging.debug("something wrong in input")

    def _save_action(self, params, response):
        logging.info(params)
        self._driver.find_element_by_xpath('//*[@class="update-btn btn"]').click()

    def _closewindow_action(self, params, response):
        self._driver.find_element_by_xpath('//*[@class="close-btn"]').click()

    def _close_action(self, params, response):
        logging.info(params)
        self._driver.save_screenshot("screenshot.png")
        self._stop_event.set()
        self._driver.close()
        del pool[self._session_id]

    def _wait_for_menu_to_load(self):
        WebDriverWait(self._driver, 30).until(EC.invisibility_of_element_located(
            (By.XPATH, '//*[@name="catalogItem"]/..//*[@class="menu-category-list"]/span/../..')))

    # private utility methods .................................................

    def _handle_login(self, params):
        logging.debug("Handling login")
        self._driver.maximize_window()
        elm_input = self._driver.find_element_by_xpath("//input[@name='email']")
        elm_input.send_keys(email)
        elm_password = self._driver.find_element_by_id('password')
        elm_password.send_keys(password)
        # elm_login = self._driver.find_element_by_xpath("//*[@id='btn-login']")
        # elm_login.click()
        elm_password.send_keys(Keys.ENTER)

    def _extention_details(self,params):
        WebDriverWait(self._driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//input[@formcontrolname="extension_number"]')))
        data = ast.literal_eval(params['data'])
        caller_number = data['caller_number']
        elm_phone_number = self._driver.find_element_by_xpath("//input[@placeholder='xxxx']")
        elm_phone_number.send_keys(caller_number)
        elm_proceed_btn = self._driver.find_element_by_xpath("//a[@class='btn-proceed'][text()='Proceed']").click()

    def _wait_for_customer_to_dial_in(self):
        logging.info("Waiting for customer to dial in ... ")
        # For now waiting for long time. But we should be using above implicitly_wait
        # self._driver.implicitly_wait(30)
        #
        # Notice extra space before and after "Waiting for Customer" message
        WebDriverWait(self._driver, 30).until(EC.invisibility_of_element_located(
            (By.XPATH, "//*[text()='Waiting for Customer'][@class='no-customer-active-message'] | //div[text()=' Waiting For Customer '][@class='no-caller-active']")))

    def _run_watch_loop(self, response):
        logging.info("Hello Customer")
        while not self._stop_event.is_set():
            body = {
                'task_type': "ResponseTask",
                'session_id': response.session_id
            }
            selenium_response = SeleniumResponse()
            try:
                selenium_response.parse(self._driver)
            except (StaleElementReferenceException, InvalidSessionIdException):
                # Don't fail for StaleElementReferenceException. Retry it again
                #
                # Don't fail for InvalidSessionIdException. This is when browser
                # session is closed (because of STOP) but thread is still running.
                continue
            # body['data'] = json.dumps(selenium_response.__dict__)
            body['data'] = json.dumps(selenium_response, default=lambda o: o.__dict__)
            body['update_time'] = int(round(time.time() * 1000))
            self._send_response(**body)
            print(self._send_response(**body))
            time.sleep(1)

    @contextlib.contextmanager
    def wait_for_page_load(self, timeout=30):
        #self.log.debug("Waiting for page to load at {}.".format(self._driver.current_url))
        old_page = self._driver.find_element_by_tag_name('html')
        yield
        WebDriverWait(self, timeout).until(staleness_of(old_page))


    def page_has_loaded(self):
        #self.log.info("Checking if {} page is loaded.".format(self._driver.current_url))
        page_state = self._driver.execute_script('return document.readyState;')
        return page_state == 'complete'




    def _send_response(self, **kwargs):
        if self._previous_response != kwargs['data']:
            self._previous_response = kwargs['data']
            # print(kwargs['data'])
            Task.add_response_task(**kwargs)

