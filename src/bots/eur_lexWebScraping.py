import os
import requests
from selenium import webdriver
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


class EurWebScraper(BaseScraper):
    def __init__(self, key_words: List[str], base_url: str, limited_page: int, driver):
        """
        EurWebScraper sınıfı BaseScraper'dan miras alır.
        """
        # BaseScraper sınıfının __init__ fonksiyonunu çağırıyoruz
        super().__init__(key_words, base_url, limited_page, driver, site_name="eur_lex")

    def search_for_keyword(self, keyword: str):
        """
        Belirli bir anahtar kelimeyi arar.
        """
        self.logger.info(f"Searching for keyword: {keyword}")
        search_box = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "QuickSearchField"))
        )
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(1)

    def sort_by_last_modified(self):
        """
        Arama sonuçlarını en son değiştirilme tarihine göre sıralar.
        """
        self.logger.info("Sorting results by last modified date.")
        try:
            sort_by_select = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[contains(@id, 'sortOne_top')]")
                )
            )
            sort_by_select.click()
            last_modified_option = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//option[@value='DD']"))
            )
            last_modified_option.click()
            time.sleep(1)
        except Exception as e:
            error_message = "No results found for this keyword."
            self.logger.error(f"{error_message} Error: {str(e).splitlines()[0]}")
            raise Exception(error_message)

    def get_urls(self, keyword: str, limited_pages: int) -> Tuple[
        List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Anahtar kelimeye göre PDF ve PDF olmayan URL'leri çıkarır.
        """
        pdf_urls = []
        non_pdf_urls = []

        self.driver.get(self.base_url)
        time.sleep(1)

        try:
            self.search_for_keyword(keyword)
            self.sort_by_last_modified()
            self.current_page = 1
            while True:
                self.logger.info(f"Processing page {self.current_page}")
                search_results = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[@id='EurlexContent']//div[@class='SearchResult']")
                    )
                )

                pdf_urls.extend(self.extract_links(search_results, 'pdf'))
                non_pdf_urls.extend(self.extract_links(search_results, 'html'))

                if not self.click_next_button(limited_pages):
                    break

        except Exception as e:
            self.log_error(e, self.driver.current_url)

        return pdf_urls, non_pdf_urls

    def extract_links(self, search_results, link_type: str) -> List[Tuple[str, str, str, str]]:
        """
        Belirtilen türdeki (PDF veya HTML) bağlantıları arama sonuçlarından çıkarır.
        """
        self.logger.info(f"Extracting {link_type} links from results.")
        urls = []
        for result in search_results:
            name_elements = result.find_elements(By.XPATH, ".//a[starts-with(@id, 'cellar_') and @href]")
            links = result.find_elements(By.XPATH, f".//a[starts-with(@title, '{link_type}') and @href]")
            dates = result.find_elements(By.XPATH, ".//dd[contains(text(), '/')]")

            for name_element, date, link in zip(name_elements, dates, links):
                name_text = name_element.text.strip()[:20]
                date_text = self.format_date(date.text.strip())
                day, month, year = date_text.split('-')
                date_text = f"{year}-{month}-{day}"

                url = link.get_attribute("href")
                description_text = name_element.text.strip()

                unique_name = f"{date_text}-{name_text}".replace('/', '_').replace(':', '').replace(' ', '_')

                counter = 1
                base_name = unique_name
                while any(unique_name in item for item in urls):
                    unique_name = f"{base_name}-{counter}"
                    counter += 1

                urls.append((url, date_text, unique_name, description_text))

        return urls

    def click_next_button(self, limited_page: int) -> bool:
        """
        Sonraki sayfa düğmesine tıklayıp tıklamamak için kontrol yapar.
        """
        try:
            if limited_page == 0:
                limited_page = float('inf')

            if self.current_page < limited_page:
                self.current_page += 1
                next_button = self.driver.find_element(By.XPATH, "//div[@class='ResultsTools']//a[@title='Next Page']")
                if 'disabled' not in next_button.get_attribute('class') and next_button.get_attribute(
                        'href') != "javascript:;":
                    next_button.click()
                    time.sleep(1)
                    return True
        except Exception as e:
            self.logger.error(f"Error clicking next button: {e}")
        return False

    def format_date(self, date_text: str) -> str:
        """
        Formats the date text by removing unwanted characters.

        Args:
            date_text (str): The original date text.

        Returns:
            str: The formatted date text.
        """
        if ";" in date_text:
            return date_text.split(';')[0].strip().replace('/', '-')
        return date_text.replace('/', '-')

