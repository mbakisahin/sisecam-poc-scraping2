import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
import json
import logging
from config import setup_shared_logger

from src.utils.baseScrapper import BaseScraper


class Bundesanzeiger(BaseScraper):
    def search_for_keyword(self, keyword):
        """
        Searches for the given keyword on the specific website.

        Args:
            keyword (str): The keyword to search for.
        """
        try:
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='text' and @placeholder='Suchbegriff eingeben']"))
            )

            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            self.logger.info(f"Keyword '{keyword}' successfully entered and search initiated.")
        except Exception as e:
            self.logger.error(f"Failed to enter keyword '{keyword}' in the search box: {str(e)}")

    def get_urls(self, keyword: str, limited_page: int) -> Tuple[
        List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Retrieves URLs from the search results for the specific website and enters each URL for further data extraction.

        Args:
            keyword (str): The keyword to search for.
            limited_page (int): The maximum number of pages to process. If 0, processes all pages.

        Returns:
            Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
            A tuple containing two lists: one for PDF URLs and another for non-PDF URLs.
            Each tuple in the lists contains:
                - link (str): The URL of the document.
                - formatted_date (str): The date the document was published or last modified, formatted as YYYY-MM-DD.
                - name (str): The name or title of the document.
                - description_text (str): A brief description or summary of the document.
        """
        pdf_urls = []
        non_pdf_urls = []
        matching_links = []

        self.driver.get(self.base_url)

        self.accept_cookies_button()
        self.search_for_keyword(keyword)
        self.option_100()

        page_number = 1
        if limited_page == 0:
            limited_page = float('inf')  # If limited_page is 0, allow infinite pages to be processed.

        while page_number <= limited_page:
            self.logger.info(f"Processing page {page_number}")

            row_elements = self.driver.find_elements(By.XPATH,
                                                     "//div[contains(@class, 'container result_container global-search')]//div[@class='row back' or @class='row']")

            try:

                for row_index in range(len(row_elements) - 1):
                    row_elements = self.driver.find_elements(By.XPATH,
                                                             "//div[contains(@class, 'container result_container global-search')]//div[@class='row back' or @class='row']")
                    current_row = row_elements[row_index]

                    name = self.extract_name_from_row(current_row)
                    date = self.extract_date_from_row(current_row)
                    url, description = self.extract_url_from_row(current_row)
                    if url == "":
                        continue

                    unique_name = f"{date}-{name}".replace('/', '_').replace(':', '').replace(' ', '_').replace('\n', '_')

                    # Ensure the name is unique
                    counter = 1
                    base_name = unique_name
                    while any(unique_name in item for item in matching_links):
                        unique_name = f"{base_name}-{counter}"
                        counter += 1

                    # If the URL is a PDF URL, add it to pdf_urls list
                    if description == "This is a PDF URL.":
                        pdf_urls.append((url, date, unique_name, description))  # Add to pdf_urls if it's a PDF
                    else:
                        non_pdf_urls.append((url, date, unique_name, description))  # Otherwise add to non_pdf_urls

                    # Go back to the main page and find row_elements again
                    self.driver.back()
                    self.logger.info("\n**************************************************\n")

                # Page navigation
                try:
                    next_button = self.driver.find_elements(By.XPATH,
                                                            "//a[@class='page-nav' and contains(@title, 'Zur nächsten Seite')]")
                    if next_button and next_button[0].get_attribute('href'):
                        next_button[0].click()  # Move to the next page
                        page_number += 1
                    else:
                        self.logger.info("Reached the last page. No href attribute found for the 'Next' button.")
                        break  # Stop the loop if there's no href attribute for the next button
                except Exception as e:
                    self.logger.error(f"Next button could not be found or clicked: {e}. Ending the loop.")
                    break  # Stop the loop in case of an error

                # Log the total number of PDF and non-PDF URLs found
                self.logger.info(f"Total PDF URLs found: {len(pdf_urls)}")
                self.logger.info(f"Total non-PDF URLs found: {len(non_pdf_urls)}")
            except Exception as e:
                self.logger.info(f"{e}")


        return pdf_urls, non_pdf_urls

    def is_security_check_present(self) -> bool:
        """
        Checks if the security check (e.g., 'Sicherheitsabfrage') is present on the page.

        Returns:
            bool: True if security check is present, False otherwise.
        """
        try:
            security_check_element = self.driver.find_elements(By.XPATH, "//h3[contains(text(), 'Sicherheitsabfrage')]")
            if security_check_element:
                self.logger.warning("Security check detected.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to check for security check: {str(e)}")
            return False

    def extract_additional_data(self) -> str:
        """
        Extracts additional data from the newly opened page after clicking on a URL.

        Returns:
            str: Extracted additional data from the page (e.g., document text, metadata).
        """
        try:
            heading_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1"))
            )
            additional_data = heading_element.text.strip()
            self.logger.info(f"Extracted additional data: {additional_data}")
            return additional_data
        except Exception as e:
            self.logger.error(f"Failed to extract additional data: {str(e)}")
            return ""

    def extract_name_from_row(self, row_element) -> str:
        """
        Extracts the name or title from a given row element.

        Args:
            row_element (WebElement): The row element to extract the name from.

        Returns:
            str: The extracted name or title.
        """
        try:
            name_element = row_element.find_element(By.CLASS_NAME, "first")
            name = name_element.text.strip()
            return name
        except Exception as e:
            self.logger.error(f"Failed to extract name from row: {str(e)}")
            return ""

    def extract_url_from_row(self, row_element) -> Tuple[str, str]:
        """
        Extracts the URL from a given row element by simulating a click if necessary.
        Also extracts the description text or PDF URL from the new page.

        Args:
            row_element (WebElement): The row element to extract the URL from.

        Returns:
            Tuple[str, str]: The extracted URL and either description text or the PDF URL.
        """
        try:
            url_element = row_element.find_element(By.TAG_NAME, "a")
            url_element.click()

            # Check for security check
            if self.is_security_check_present():
                self.logger.warning(f"Security check found, skipping URL: {url_element}")
                self.driver.back()
                return "", ""

            # Check if it's a PDF
            pdf_url = self.extract_pdf_url()
            if pdf_url:
                self.logger.info(f"Extracted PDF URL: {pdf_url}")
                return pdf_url, "This is a PDF URL."

            # If it's not a PDF, extract the description text
            description_text = self.extract_description_text()

            # Extract the new URL from the newly opened page
            new_url = self.driver.current_url
            self.logger.info(f"Extracted URL after click: {new_url}")

            return new_url, description_text
        except Exception as e:
            self.logger.error(f"Failed to extract URL or description: {str(e)}")
            return "", ""

    def extract_pdf_url(self) -> str:
        """
        Extracts the PDF URL from the currently opened page if available.

        Returns:
            str: The extracted PDF URL if found, else an empty string.
        """
        try:
            # Search for the PDF link with a general XPath
            pdf_element = self.driver.find_element(By.XPATH,
                                                   "//a[contains(@aria-label, 'Publikation im PDF-Format öffnen')]")
            pdf_url = pdf_element.get_attribute("href")
            return pdf_url
        except Exception as e:
            self.logger.error(f"No PDF link found")
            return ""

    def extract_description_text(self) -> str:
        """
        Extracts the description text from the currently opened page.

        Returns:
            str: The extracted description text.
        """
        try:
            # Retrieve the content of the tbody element
            description_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//tbody"))
            )
            description_text = description_element.text.strip()
            return description_text
        except Exception as e:
            self.logger.error(f"Failed to extract description text: {str(e)}")
            return ""

    def extract_date_from_row(self, row_element) -> str:
        """
        Extracts the date from a given row element.

        Args:
            row_element (WebElement): The row element to extract the date from.

        Returns:
            str: The extracted date, formatted as YYYY-MM-DD.
        """
        try:
            date_element = row_element.find_element(By.CLASS_NAME,
                                                    "date")
            raw_date = date_element.text.strip()
            formatted_date = self.format_date(raw_date)
            return formatted_date
        except Exception as e:
            self.logger.error(f"Failed to extract date from row: {str(e)}")
            return ""

    def format_date(self, raw_date: str) -> str:
        """
        Formats a raw date string into YYYY-MM-DD format.

        Args:
            raw_date (str): The raw date string.

        Returns:
            str: The formatted date string.
        """
        try:
            day, month, year = raw_date.split('.')
            return f"{year}-{month}-{day}"
        except Exception as e:
            self.logger.error(f"Failed to format date: {str(e)}")
            return raw_date

    def option_100(self):
        """
        Selects the option to display 100 results per page.
        """
        try:
            dropdown_arrow = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "select2-selection__arrow"))
            )
            dropdown_arrow.click()
        except Exception as e:
            self.logger.error("Dropdown arrow not found or not clickable:", e)

        try:
            option_100 = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/span/span/span[2]/ul/li[text()='100']"))
            )
            option_100.click()
            self.logger.info("Option 100 per page selected")
        except Exception as e:
            self.logger.error("Option 100 per page not found or not clickable:", e)

    def accept_cookies_button(self):
        """
        Accepts the cookies on the website.
        """
        try:
            accept_cookies_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allen zustimmen')]"))
            )
            accept_cookies_button.click()
            self.logger.info("Cookies accepted")
        except Exception as e:
            self.logger.error("Cookie acceptance not found or not clickable:", e)

