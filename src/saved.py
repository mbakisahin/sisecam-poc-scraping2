from src.bots import EchaWebScraper, EurWebScraper, ResmiWebScraper, Enhesa
from selenium import webdriver
from src.bots.bundesanzeigerWebScraping import Bundesanzeiger
from src.bots.foodPackingForumWebScrapping import FoodPackingForum


class ScriptRunner:

    def __init__(self, script_keywords_file):
        """
        Initialize the ScriptRunner.

        Parameters:
        script_keywords_file (str): Path to the text file containing script names,
                                    links, and associated keywords.
        """
        self.script_keywords_file = script_keywords_file

    def read_scripts_from_file(self, filepath):
        """
        Read scripts information from a text file with the specified format.

        Parameters:
        filepath (str): Path to the text file containing scripts information.

        Returns:
        list: A list of tuples where each tuple contains:
              (script name, link, list of keywords, limited page number).
        """
        scripts = []
        current_script = None
        keywords = []

        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith("Name:"):
                if current_script:
                    scripts.append((current_script[0], current_script[1], keywords, current_script[2]))
                script_name = line.split("Name:")[1].strip()
                current_script = [script_name, None, None]
                keywords = []
            elif line.startswith("Link:"):
                current_script[1] = line.split("Link:")[1].strip()
            elif line.startswith("Limited page number:"):
                current_script[2] = int(line.split("Limited page number:")[1].strip())
            elif line.startswith("Keywords:"):
                continue
            elif line:
                keywords.append(line)

        # Son script'i ekle
        if current_script:
            scripts.append((current_script[0], current_script[1], keywords, current_script[2]))

        return scripts

    def run_scripts(self, scripts):
        """
        Run the given scripts with their respective links and keywords.

        Parameters:
        scripts (list): A list of tuples where each tuple contains:
                        (script name, link, list of keywords, limited page number).
        """
        for script, link, keywords, limited_page in scripts:
            self.run_script(script, link, keywords, limited_page)

    def run_script(self, script, link, keywords, limited_page):
        """
        Run the specified script with the provided link and keywords.

        Parameters:
        script (str): The name of the script to run.
        link (str): The base URL or link to be used in the script.
        keywords (list): A list of keywords to process with the script.
        limited_page (int): The page limit for scraping (if applicable).
        """

        for keyword in keywords:

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--window-size=1920,1080")

            driver = webdriver.Chrome(options=chrome_options)

            print(f'Running {script} with link {link} and keyword: {keyword}')

            if script == 'echaWebScraping.py':
                scraper = EchaWebScraper(key_words=[keyword], base_url=link, limited_pages=limited_page, driver=driver)
                scraper.start()
            elif script == 'eur_lexWebScraping.py':
                scraper = EurWebScraper(key_words=[keyword], base_url=link, limited_page=limited_page, driver=driver)
                scraper.start()
            elif script == 'resmigazeteWebScraping.py':
                scraper = ResmiWebScraper(key_words=[keyword], base_url=link, limited_page=limited_page, driver=driver)
                scraper.start()
            elif script == 'bundesanzeigerWebScraping.py':
                scraper = Bundesanzeiger(key_words=[keyword],
                                             base_url=link,
                                             limited_pages=limited_page,
                                             driver=driver,
                                             site_name="bundesanzeiger"
                )
                scraper.start()
            elif script == 'foodPackingForumWebScrapping.py':
                scraper = FoodPackingForum(key_words=[keyword],
                                             base_url=link,
                                             limited_pages=limited_page,
                                             driver=driver,
                                             site_name="foodPackingForum"
                )
                scraper.start()
            elif script == 'enhesaWebScraping.py':
                scraper = Enhesa(key_words=[keyword],
                                             base_url=link,
                                             limited_pages=limited_page,
                                             driver=driver,
                                             site_name="enhesa"
                )
                scraper.start()

