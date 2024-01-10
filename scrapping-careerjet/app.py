import json
import logging
from time import sleep, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


class ScrappingCareerjet:
    def __init__(self, job, location, page_job=100):
        """
        Initialize MediaDownloader with job, location, and total pages.
        """
        self.pekerjaan = job
        self.lokasi = location
        self.total_page = page_job
        self.list_url = []
        self.list_detail = []
        self.chrome = ChromeDriverManager().install()
        self.runtime = None

    def driver_init(self):
        """
        Initialize and configure the WebDriver.
        """
        # Turn off the selenium log
        selenium_logger = logging.getLogger("selenium")
        selenium_logger.setLevel(logging.WARNING)
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger.setLevel(logging.INFO)

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"

        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--headless")  # browser in background
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        service = Service(executable_path=self.chrome)
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def scraping_list_pekerjaan(self):
        """
        Scrape the list of job URLs.
        """
        driver = self.driver_init()

        for num in range(1, self.total_page + 1):
            set_page = f"https://www.careerjet.id/search/jobs?s={self.pekerjaan}&l={self.lokasi}&p={num}"
            driver.get(set_page)

            page_source = driver.page_source
            target = "No results found"

            # Find the text on the webpage
            check_found = target in page_source
            if check_found:
                break

            soup = BeautifulSoup(page_source, "html.parser")

            metas = soup.find_all(
                "article", {"class": "job clicky"}, {"data-url": True}
            )

            for meta in metas:
                urls = meta.find("a").get("href") if metas is not None else ""
                self.list_url.append("https://www.careerjet.id" + urls)

        print("Finished scraping the list of job URLs.")
        print("Total URL:", len(self.list_url))
        driver.close()

    def scraping_detail_pekerjaan(self):
        """
        Scrape details of each job from the list of URLs.
        """
        driver = self.driver_init()

        if self.list_url:
            total_list_url = len(self.list_url)
            with tqdm(total=total_list_url, desc="Processing") as pbar:
                for url in self.list_url:
                    sleep(0.1)
                    pbar.update(1)

                    driver.get(url)

                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="job"]/div/section[1]')
                            )
                        )

                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, "html.parser")

                        metas = soup.find("article", {"id": "job"})

                        title = (
                            metas.find("header").find("h1") is not None
                            and metas.find("header").find("h1").get_text()
                            or "-"
                        )

                        company = (
                            metas.find("header").find("p", {"class": "company"})
                            is not None
                            and metas.find("header")
                            .find("p", {"class": "company"})
                            .get_text()
                            or "-"
                        )

                        detail = (
                            metas.find("ul", {"class": "details"}).get_text().split()
                        )

                        description = (
                            metas.find("section", {"class": "content"}) is not None
                            and metas.find("section", {"class": "content"}).get_text()
                            or "-"
                        )

                        self.list_detail.append(
                            {
                                "title": title,
                                "company": company,
                                "location": detail[0],
                                "contract_type": detail[1],
                                "working_hours": detail[2],
                                "description": " ".join(description.split()),
                            }
                        )

                    except Exception as e:
                        print(f"An exception occurred: {type(e).__name__}")
                        print("Timeout Exception: Page did not load within 15 seconds.")
        driver.close()

    def run_scraper(self):
        """
        Run the scraper.
        """
        start_time = time()

        self.scraping_list_pekerjaan()
        self.scraping_detail_pekerjaan()

        # End time
        end_time = time()

        # Calculate the runtime in seconds
        runtime_seconds = end_time - start_time

        # Convert seconds to hours, minutes, and seconds
        hours, remainder = divmod(runtime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.runtime = (
            f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
        )

    def data(self):
        """
        Convert the scraped job details to JSON.
        """
        json_data = json.dumps(self.list_detail)
        return json_data


if __name__ == "__main__":
    PEKERJAAN = "python"
    LOKASI = "indonesia"

    media = ScrappingCareerjet(PEKERJAAN, LOKASI)
    media.run_scraper()

    with open("output.json", "w", encoding="utf-8") as file:
        file.write(media.data())

    print("Runtime:", media.runtime)
