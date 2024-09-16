import os
import time
import requests
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from typing import List, Tuple
from bs4 import BeautifulSoup
from config import setup_shared_logger
from src.utils.baseScrapper import BaseScraper


class FoodPackingForum(BaseScraper):
    def search_for_keyword(self, keyword):
        """
        Searches for the given keyword on the specific website.

        Args:
            keyword (str): The keyword to search for.
        """
        try:
            element = self.driver.find_element(By.ID, 'menu-main-menu-2016')
        except NoSuchElementException:
            print("element not found")

        style = element.get_attribute('style')

        if style != "display: none;":
            element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "search-toggle-wrapper")))
            actions = ActionChains(self.driver)
            actions.move_to_element(element).click().perform()

        search_box = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form[role='search'] input.form-control.top-search-field"))
        )
        time.sleep(2)
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(10)

    def get_urls(self, keyword: str, limited_page: int) -> Tuple[
        List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Retrieves URLs from the search results for the specific website.

        Args:
            keyword (str): The keyword to search for.
            limited_pages (int): The maximum number of pages to process.

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

        self.driver.get(self.base_url)
        time.sleep(5)

        self.search_for_keyword(keyword)
        # Site-specific URL retrieval logic goes here.
        if limited_page == 0:
            limited_page = 999
        for page in range(0, limited_page):
            print(f"Scraping page {page}")
            try:
                articles_exist = self.driver.find_elements(By.CSS_SELECTOR, ".blog-entry")
                print(articles_exist)
                if len(articles_exist) == 0:
                    break
            except:
                pass
            # Find all article elements
            articles = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//article[contains(@class, 'blog-entry')]"))
            )
            try:
                for article in articles:
                    # Extract link and title
                    title_element = article.find_element(By.CLASS_NAME, "entry-title")
                    link = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                    name = title_element.text.strip()
                    # Extract date
                    date_element = article.find_element(By.CLASS_NAME, "entry-date")
                    formatted_date = self.format_date(date_element.text.strip())
                    unique_name = f"{formatted_date}-{name}".replace('/', '_').replace(':', '').replace(' ', '_').replace('\n', '_')

                    # Extract description
                    description_element = article.find_element(By.CLASS_NAME, "entry-content")
                    description_text = description_element.text.strip()

                    # Append to appropriate list
                    if link.lower().endswith('.pdf'):
                        pdf_urls.append((link, formatted_date, unique_name, description_text))

                    non_pdf_urls.append((link, formatted_date, unique_name, description_text))
            except:
                pass
            # Check if there's a next page and navigate to it
            try:
                next_page = self.driver.find_element(By.CSS_SELECTOR, "a.nextpostslink")
                next_page.click()
                time.sleep(3)  # Wait for the new page to load
            except NoSuchElementException:
                print("No more pages to scrape")
                break
        if len(non_pdf_urls) > 0 :
            non_pdf_urls_desc = []
            drivers = self.setup_driver()
            try:
                for url, date, title, _ in non_pdf_urls:
                    print(url)
                    new_description = self.fetch_article_content(drivers, url)
                    non_pdf_urls_desc.append((url, date, title, new_description))
                    time.sleep(2)  # Add a delay between requests to be polite
            finally:
                drivers.quit()
        else:
            non_pdf_urls_desc = non_pdf_urls

        return pdf_urls, non_pdf_urls_desc

    def fetch_article_content(self, driver, url: str) -> str:
        """
        Fetch all content in specify url to add as decriptions

        Args:
            driver : Headless driver.
            url (str): Url to fetch content
        Returns:
            Return full content of url page.
        """
        try:
            driver.get(url)
            # Wait for the content to load
            wait = WebDriverWait(driver, 10)
            content = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "entry-content")))

            paragraphs = content.find_elements(By.TAG_NAME, "p")

            # Extract and join the text from all paragraphs
            full_content = ' '.join([p.text.strip() for p in paragraphs])
            return full_content
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return "Error fetching content"

    def format_date(self, date_string: str) -> str:
        """
        Formats the date string to YYYY-MM-DD format.
        """
        from datetime import datetime
        date_obj = datetime.strptime(date_string, "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")

    def setup_driver(self):
        """
        Setup headless driver to read all the content in the urls
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        return driver