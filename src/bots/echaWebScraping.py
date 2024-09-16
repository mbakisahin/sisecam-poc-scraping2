import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Tuple
from src.utils.baseScrapper import BaseScraper


class EchaWebScraper(BaseScraper):
    def __init__(self, key_words: List[str], base_url: str, limited_pages: int, driver):
        """
        Initializes the EchaWebScraper class with keywords for searching and Selenium WebDriver.
        """
        super().__init__(key_words, base_url, limited_pages, driver, site_name="ECHA")
        self.driver.get(self.base_url)

    def search_for_keyword(self, keyword: str):
        """
        ECHA web sitesinde anahtar kelimeyle arama yapar.
        """
        self.logger.info(f"Searching for keyword: {keyword}")
        search_box = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "SimpleSearchText"))
        )
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)

    def select_date(self, year: int, month: int, day: int):
        """
        Arama sonucunu tarih filtresi ile sınırlar.
        """
        self.logger.info(f"Selecting date: {year}-{month}-{day}")
        from_date_picker = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, '_echasearch_WAR_echaportlet_updatedFrom')]"))
        )
        from_date_picker.click()

        year_select_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'ui-datepicker-year')]"))
        )

        year_select = Select(year_select_element)
        year_select.select_by_value(str(year))

        month_select_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'ui-datepicker-month')]"))
        )
        month_select = Select(month_select_element)
        month_select.select_by_value(str(month - 1))

        day_element = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"//td[@data-handler='selectDay' and @data-month='{month - 1}' and @data-year='{year}']/a[text()='{day}']"))
        )
        day_element.click()

    def sort_by_last_modified(self):
        """
        Arama sonuçlarını "Son Düzenlenme" tarihine göre sıralar.
        """
        self.logger.info("Sorting by last modified date.")
        sort_by_select = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@id, '_echasearch_WAR_echaportlet_sortingType')]"))
        )
        sort_by_select.click()
        last_modified_option = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//option[@value='modified']"))
        )
        last_modified_option.click()

    def get_urls(self, keyword: str, limited_page: int) -> Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Arama sonuçlarından PDF ve PDF olmayan URL'leri toplar.
        """
        pdf_urls = []
        non_pdf_urls = []
        matching_links = []


        self.driver.get(self.base_url)

        try:
            self.logger.info(f"Retrieving URLs for keyword: {keyword}")
            self.search_for_keyword(keyword)
            self.select_date(2012, 8, 9)
            self.sort_by_last_modified()
            time.sleep(1)
            page_number = 1

            while True:
                self.logger.info(f"Processing page number: {page_number}")
                results = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'search-result-title')]//a[@href]"))
                )
                dates = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH,
                         "//div[contains(@class, 'search-result-title')]//a[@href]/../../following-sibling::td"))
                )
                descriptions = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'search-result-content')]"))
                )

                for result, date, description in zip(results, dates, descriptions):
                    link = result.get_attribute("href")
                    name = result.text.strip()
                    description_text = description.text.strip()

                    if link.startswith('/'):
                        link = 'https://echa.europa.eu' + link
                    formatted_date = date.text.strip().replace('/', '-')
                    day, month, year = formatted_date.split('-')
                    year = '20' + year
                    formatted_date = f"{year}-{month}-{day}"

                    unique_name = f"{formatted_date}-{name}".replace('/', '_').replace(':', '').replace(' ', '_').replace('\n',
                                                                                                                '_')

                    # Ensure the name is unique
                    counter = 1
                    base_name = unique_name
                    while any(unique_name in item for item in matching_links):
                        unique_name = f"{base_name}-{counter}"
                        counter += 1

                    if link.split('/')[-2].endswith('.pdf'):
                        pdf_urls.append((link, formatted_date, unique_name, description_text))
                    else:
                        non_pdf_urls.append((link, formatted_date, unique_name, description_text))

                self.logger.info(f"Found {len(pdf_urls)} PDF URLs and {len(non_pdf_urls)} non-PDF URLs.")

                if limited_page == 0:
                    limited_page = float('inf')

                if page_number < limited_page:
                    page_number += 1
                    next_button = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')]")
                    if next_button and 'disabled' not in next_button[0].get_attribute('class') and next_button[0].get_attribute('href') != "javascript:;":
                        next_button[0].click()
                    else:
                        break
                else:
                    break
        except Exception as e:
            self.log_error(e, self.driver.current_url)

        return pdf_urls, non_pdf_urls

