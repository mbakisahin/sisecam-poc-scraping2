import os
from datetime import datetime
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

class Enhesa(BaseScraper):
    """
    A class to scrape data from a specific website, implementing search functionality, extracting URLs, and handling
    cookies. This scraper is derived from a base scraper class and customized for the Enhesa website.
    """

    def search_for_keyword(self, keyword):
        """
        Searches for the given keyword on the specific website using the search bar.

        Args:
            keyword (str): The keyword to search for.
        """
        try:
            # Locate the search bar by 'name' attribute
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "s"))
            )
            search_box.clear()  # Clear any existing content in the search bar
            search_box.send_keys(keyword)  # Enter the keyword

            # Simulate pressing the Enter key
            search_box.send_keys(Keys.RETURN)

            self.logger.info(f"Keyword '{keyword}' is searched using Enter key.")
        except Exception as e:
            self.logger.info(f"Error in searching for the keyword: {e}")

    def get_urls(self, keyword: str, limited_page: int) -> Tuple[
        List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Retrieves URLs from the search results for the specific website. Handles both PDF and non-PDF URLs, storing
        them separately.

        Args:
            keyword (str): The keyword to search for.
            limited_page (int): The maximum number of pages to process.

        Returns:
            Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
            A tuple containing two lists: one for PDF URLs and another for non-PDF URLs.
        """
        pdf_urls = []
        non_pdf_urls = []
        matching_links = []

        # Open the base URL
        self.driver.get(self.base_url)
        self.accept_cookies()  # Accept cookies if the banner appears
        self.search_for_keyword(keyword)

        page_number = 1
        if limited_page == 0:
            limited_page = float('inf')  # If limited_page is 0, allow infinite pages to be processed.

        while page_number <= limited_page:
            self.logger.info(f"Processing page {page_number}")

            try:
                # Find the rows containing search result elements
                row_elements = self.driver.find_elements(By.XPATH,
                                                         "//div[@class='row pb-4']")

                for row_index in range(len(row_elements) - 1):
                    row_elements = self.driver.find_elements(By.XPATH,
                                                             "//div[@class='row pb-4']")
                    current_row = row_elements[row_index]
                    name = self.extract_name_from_row(current_row)
                    date = self.extract_date_from_row()
                    url, description = self.extract_url_from_row(current_row)

                    if url == "":
                        continue

                    # Generate a unique name based on the date and document name
                    unique_name = f"{date}-{name}".replace('/', '_').replace(':', '').replace(' ', '_').replace('\n', '_')

                    # Ensure the name is unique by appending a counter if necessary
                    counter = 1
                    base_name = unique_name
                    while any(unique_name in item for item in matching_links):
                        unique_name = f"{base_name}-{counter}"
                        counter += 1

                    # Categorize URLs as PDF or non-PDF
                    if url.endswith(".pdf"):
                        pdf_urls.append((url, date, unique_name, description))
                    else:
                        non_pdf_urls.append((url, date, unique_name, description))

                try:
                    # Find the "Next" button to move to the next page of results
                    next_button = self.driver.find_elements(By.XPATH,
                                                            "//a[@class='next page-numbers']")
                    if next_button and next_button[0].get_attribute('href'):
                        next_button[0].click()  # Click the "Next" button to load more results
                        page_number += 1
                    else:
                        self.logger.info("Reached the last page. No href attribute found for the 'Next' button.")
                        break  # Stop the loop if there's no next page
                except Exception as e:
                    self.logger.error(f"Next button could not be found or clicked: {e}. Ending the loop.")
                    break  # Stop the loop in case of an error

            except Exception as e:
                self.logger.error(f"Error processing row: {e}")
                break

        return pdf_urls, non_pdf_urls

    def accept_cookies(self):
        """
        Accepts cookies on the website by clicking the cookie consent button if present.
        """
        try:
            # Wait up to 20 seconds for the cookie button to become clickable
            cookie_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ccc-accept-button"))
            )
            cookie_button.click()  # Click the cookie consent button
            self.logger.info("Cookies accepted.")
        except Exception as e:
            self.logger.info(f"No cookies banner found or error in clicking: {e}")

    def extract_name_from_row(self, row):
        """
        Extracts the document name from a row element.

        Args:
            row: The WebElement representing a row in the search results.

        Returns:
            str: The name of the document.
        """
        try:
            name = row.find_element(By.XPATH, ".//h3").text
            return name.strip()
        except:
            return ""

    def extract_date_from_row(self):
        """
        Extracts the current date for the document, as the date might not always be available in the row.

        Returns:
            str: The current date in "YYYY-MM-DD" format.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        return current_date

    def extract_url_from_row(self, row):
        """
        Extracts the URL and description from a row element by navigating to the page and scraping the description.

        Args:
            row: The WebElement representing a row in the search results.

        Returns:
            Tuple[str, str]: A tuple containing the URL and the description from the page.
        """
        try:
            # Extract the href attribute from the 'a' tag
            url_element = row.find_element(By.XPATH, ".//a")
            url = url_element.get_attribute("href")

            # Navigate to the URL to extract the description
            self.driver.get(url)
            description = self.extract_description_from_page()

            # Navigate back to the search results page
            self.driver.back()

            return url, description
        except Exception as e:
            self.logger.error(f"Error while extracting URL or description: {e}")
            return "", ""

    def extract_description_from_page(self):
        """
        Extracts the description from a specific page by scraping text from sections.

        Returns:
            str: The combined text from all sections on the page.
        """
        try:
            # Find all sections with the 'b-editor' class
            section_elements = self.driver.find_elements(By.XPATH, "//section[contains(@class, 'b-editor')]")

            # Collect all text from the sections into a list
            all_text = []
            for section in section_elements:
                text = section.text.strip()  # Extract and clean the text from the section
                if text:  # Only add non-empty text
                    all_text.append(text)

            # Combine all section texts into one string
            full_text = "\n\n".join(all_text)
            return full_text
        except Exception as e:
            self.logger.error(f"Error while extracting description: {e}")
            return ""
