import asyncio
import logging
from typing import IO

import yaml
from bs4 import BeautifulSoup
from loguru import logger

from dr_dataclass import EnZhText, Practitioner, Qualification
from util import load_pages, save_dataclass_list_to_json

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# registered doctors URL; takes page number as parameter
DOCTORS_PAGE_FN = (
    lambda x: f"{config_dict['scraper']['doctors_overview']['url']}&page={x}"
)
NUM_PAGES = config_dict["scraper"]["doctors_overview"]["num_pages"]
OUTPUT_JSONFILENAME = config_dict["scraper"]["doctors_overview"]["output_path"]

# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
)
logger.add(config_dict["logpath"])


async def parse_registered_doctors_page(
    page_request: IO[str],
) -> list[Practitioner]:
    """
    Parses registered doctor page from HK Government list of registered
    medical practitioners.
    Args:
        - page_request(IO[str]): page request to parse
    Returns:
        - List of practitioners parsed from page
    """
    # make request and initialise beautiful soup object
    # page_request = make_request(page_url)
    soup = BeautifulSoup(page_request, "lxml")

    # find the first table on the page
    table = soup.find_all("table")

    # error handling if no table is found
    table = table[0]
    rows = table.find_all("tr")

    # initialise practitioner list to parse
    practitioner_list = []

    # clean rows before parsing
    # after 9th row; as that's when medical doctors' information starts
    rows = [
        [ele.text.strip() for ele in row.find_all("td")] for row in rows[9:]
    ]

    # parse columns in the rows
    for cols in rows:
        # breaks once we get to the bottom of the table
        if cols[0].startswith("« Previous"):
            break

        # parse to Practitioner object; first line is a regiration num eg. 'M17694'
        # example of format of column:
        # ['M15833', '區卓仲AU, CHEUK CHUNG', '', '', '', '香港大學內外全科醫學士MB BS (HK)', '', '2008']
        if cols[0][0] == "M" and len(cols[0]) == 6:
            practitioner = Practitioner(
                registration_no=cols[0],
                name=EnZhText(cols[1]),
                address=EnZhText(cols[3]),
                qualifications=[
                    Qualification(nature_tag=cols[5], year=cols[7])
                ],
            )
            practitioner_list.append(practitioner)

        else:
            practitioner_list[-1].qualifications.append(
                Qualification(nature_tag=cols[0], year=cols[2])
            )

    return practitioner_list


async def main():
    """
    Parse overview of doctors page asynchronously and saves to JSON file.
    """
    urls_to_parse = [
        DOCTORS_PAGE_FN(page_num) for page_num in range(NUM_PAGES + 1)
    ]
    logger.info(f"Parsing {len(urls_to_parse)} pages asynchronously.")
    full_practitioner_list = await load_pages(
        urls_to_parse, parse_registered_doctors_page
    )

    logger.info(f"Loaded {NUM_PAGES} pages. Saving to {OUTPUT_JSONFILENAME}")
    save_dataclass_list_to_json(full_practitioner_list, OUTPUT_JSONFILENAME)


if __name__ == "__main__":
    asyncio.run(main())
