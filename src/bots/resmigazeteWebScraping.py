import os
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
import json
import logging

from config import setup_shared_logger
from src.utils.baseScrapper import BaseScraper


class ResmiWebScraper(BaseScraper):
    def __init__(self, key_words: List[str], base_url: str, limited_page: int, driver):
        """
        ResmiWebScraper sınıfı BaseScraper'dan miras alır.
        """
        super().__init__(key_words, base_url, limited_page, driver, site_name="resmigazete")

    def search_for_keyword(self, keyword: str):
        """
        Belirli bir anahtar kelimeyi arar.
        """
        self.logger.info(f"Searching for keyword: {keyword}")
        search_button = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "body > div.container-fluid.mb-3 > div > div > div > div > div.col-12.col-md-8 > div > button"))
        )
        search_button.click()
        time.sleep(1)

        search_bar = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "genelaranacakkelime"))
        )
        search_bar.click()
        search_bar.clear()
        search_bar.send_keys(keyword)
        time.sleep(1)
        search_bar.send_keys(Keys.RETURN)
        time.sleep(1)

    def get_urls(self, keyword: str, limited_pages: int) -> Tuple[
        List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Anahtar kelimeye göre PDF ve PDF olmayan URL'leri çıkarır.
        """
        matching_links = []
        pdf_urls = []
        non_pdf_urls = []

        self.driver.get(self.base_url)

        self.search_for_keyword(keyword)
        current_page = 1
        while True:
            self.logger.info(f"Processing page {current_page}")
            try:
                result_links = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//table[@id='filterTable']//a[@href]"))
                )

                dates = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH,
                         "//table[@id='filterTable']//a[@href]/../../following-sibling::td"))
                )
                dates = [td.text for td in dates if len(td.text.strip()) == 10]

                for result, date in zip(result_links, dates):
                    result.click()
                    time.sleep(1)

                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    links = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//a[@href]")))

                    for link in links:
                        link_url = link.get_attribute("href")
                        description_text = link.text.strip()

                        if re.search(r'\b' + re.escape(keyword) + r'\b', description_text):
                            name_text = link.text.strip()[:20]
                            date_text = self.format_date(date)
                            day, month, year = date_text.split('-')
                            date_text = f"{year}-{month}-{day}"

                            description_text = link.text.strip()

                            # Benzersiz dosya adını oluştur
                            unique_name = f"{date_text}-{name_text}"
                            unique_name = unique_name.replace('/', '_').replace(':', '').replace(' ', '_')

                            # Dosya adının benzersiz olduğundan emin ol
                            counter = 1
                            base_name = unique_name
                            while any(unique_name in item for item in matching_links):
                                unique_name = f"{base_name}-{counter}"
                                counter += 1

                            if link_url.endswith('.pdf'):
                                pdf_urls.append((link_url, date_text, unique_name, description_text))
                            else:
                                non_pdf_urls.append((link_url, date_text, unique_name, description_text))

                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"An error occurred: {e}. Continuing with the next iteration.")

            try:
                if limited_pages == 0:
                    limited_pages = float('inf')

                if current_page < limited_pages:
                    current_page += 1
                    next_button = self.driver.find_elements(By.ID, "filterTable_next")
                    if next_button and 'paginate_button page-item next disabled' not in next_button[0].get_attribute(
                            'class') and next_button[0].get_attribute('href') != "javascript:;":
                        next_button[0].click()
                        time.sleep(5)
                    else:
                        break
                else:
                    break
            except Exception as e:
                self.logger.error(f"Next button could not be found or clicked: {e}. Ending the loop.")
                break

        return pdf_urls, non_pdf_urls

    def format_date(self, date_text: str) -> str:
        """
        Tarih metnini istenen formata göre düzenler.
        """
        if ";" in date_text:
            return date_text.split(';')[0].strip().replace('.', '-')
        return date_text.replace('.', '-')

