import asyncio
import json
import logging
from typing import IO

import yaml
from bs4 import BeautifulSoup
from loguru import logger

from scrape_util import load_pages, save_dataclass_list_to_json

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# detailed registered doctors url; takes registration number as parameter.
DOCTORS_PAGE_FN = (
    lambda x: f"{config_dict['scraper']['doctors_detail']['url']}{x}"
)
INPUT_JSON_PATH = config_dict["scraper"]["doctors_overview"]["output_path"]
OUTPUT_JSON_PATH = config_dict["scraper"]["doctors_detail"]["output_path"]

# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
)
logger.add(config_dict["logpath"])


async def parse_detailed_doctors_page(page_request: IO[str]):
    # make request and initialise beautiful soup object
    # page_request = make_request(page_url)
    soup = BeautifulSoup(page_request, "lxml")

    # find the first table on the page
    table = soup.find_all("table")

    # error handling if no table is found
    table = table[0]
    rows = table.find_all("tr")

    for row in rows[:]:
        # parse individual columns
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]

        # breaks once we get to the bottom of the table
        if cols[0].startswith("* A registered"):
            break

        # skip empty rows
        if len(cols) == 1 and cols[0] == "":
            continue

        print(cols)

    return


async def main():
    """
    - Go through the output of scraped_doctors_overview.
    - Load page of detailed information about doctors to get specialist information, if any.
    - Also can run assertion checks on the data folder against doctors' described details.
    """
    logger.info(f"Loading doctors jsonfile: {INPUT_JSON_PATH}.")
    with open(INPUT_JSON_PATH, "r") as json_file:
        doctor_data = json.load(json_file)

    print("$$" * 80)
    logging.info(f"Looping through {len(doctor_data)} doctor records.")
    for idx, doctor in enumerate(doctor_data):
        print(doctor)

        doctor_url = DOCTORS_PAGE_FN(doctor["registration_no"])

        await load_pages([doctor_url], parse_detailed_doctors_page)

        print("><" * 80)
        if idx == 2:
            break


if __name__ == "__main__":
    asyncio.run(main())
