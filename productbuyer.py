from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import FirefoxOptions

import os
import re
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

USER = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")


class ProductBuyer:

    def __init__(self, item_id):
        logger.info("Starting Firefox")
        opts = FirefoxOptions()
        opts.add_argument("--headless")
        self.driver = webdriver.Firefox(firefox_options=opts)
        self.driver.maximize_window()
        self.item_id = item_id
        self.url = f"https://www.amazon.co.uk/dp/{item_id}"

    def get_price(self):
        logger.info(f"Visiting {self.url}")
        for attempt in range(1, 21):
            self.driver.get(self.url)
            logger.info(
                f"Attempting to retrieve price, attempt {attempt} of 20")
            try:
                price_str = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located((By.ID, "priceblock_ourprice"))).get_attribute('innerText')  # Get the price element
            except:
                logger.info(f"Failed to find price")
            else:
                break
        else:
            logger.info(
                f"Price not found (Likely unavailable) - Closing Firefox")
            self.driver.close()
            return None

        logger.info(f"Price found!")
        # Extract the numerical data
        price = re.findall(r"\d+\.\d+", price_str)[0]
        return float(price)

    def buy(self):
        """
        Click the cookies accept button then click 'Buy Now' button
        """
        logger.info("Attempting to click 'Buy Now'")
        # self.driver.get(self.url) # Navigate to item
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.NAME, "accept"))).click()  # Click the cookie accept button
        except:
            pass
        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "submit.buy-now"))).click()  # Click Buy Now

    def login(self):
        logger.info("Loging in")
        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "email"))).send_keys(USER, Keys.ENTER)  # Enter Email
        self.driver.implicitly_wait(2)
        self.driver.find_element_by_id('ap_password').send_keys(
            PASSWORD, Keys.ENTER)  # Enter password

    def confirm(self):
        logger.info("Submitting the order")
        self.driver.find_element_by_id(
            "submitOrderButtonId").click()  # Submit the order
        self.driver.implicitly_wait(20)

    def close(self):
        logger.info("Closing Firefox")
        self.driver.quit()
