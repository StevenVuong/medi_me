import asyncio
import json
import logging
from typing import IO

import yaml
from bs4 import BeautifulSoup
from loguru import logger

from dr_dataclass import Practitioner, Qualification
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


async def parse_rows(rows: list[list[str]]) -> Practitioner:
    # initialise a dict to store practitioners information
    practitoner_info = {}

    # parse columns in rows
    for cols in rows:
        # breaks once we get to the bottom of the table
        if cols[0].startswith("* A registered"):
            break

        # match columns against text to parse into dataclass attributes
        match cols[0]:
            case "姓名Name":
                practitoner_info["name"] = cols[-1]

            case "註冊地址Registered Address*":
                practitoner_info["address"] = cols[-1]

            # can add registration num for general and specialty
            case "註冊編號Registration No.":
                if "registration_no" not in practitoner_info:
                    practitoner_info["registration_no"] = cols[-1]
                else:
                    practitoner_info["specialty_registration_no"] = cols[-1]

            # can either be for general registration or specialty registration
            case "資格性質及年份Nature of Qualification and Year":
                # if we don't have general qualification; add that first
                if "qualifications" not in practitoner_info:
                    practitoner_info["qualifications"] = [
                        Qualification(nature_tag=cols[-2], year=cols[-1])
                    ]

                # if we have qualification; add to specialty
                else:
                    practitoner_info[
                        "speciality_qualification"
                    ] = Qualification(nature_tag=cols[-2], year=cols[-1])

            case "專科Specialty":
                practitoner_info["specialty_name"] = cols[-1]

            # TODO: If blank; to append qualifications, -2 and -1

    return [Practitioner(**practitoner_info)]  # return list to extend


async def parse_detailed_doctors_page(page_request: IO[str]) -> Practitioner:
    # make request and initialise beautiful soup object
    # page_request = make_request(page_url)
    soup = BeautifulSoup(page_request, "lxml")

    # find the first table on the page
    table = soup.find_all("table")

    # error handling if no table is found
    table = table[0]
    rows = table.find_all("tr")

    # parse individual columns in rows
    rows = [[ele.text.strip() for ele in row.find_all("td")] for row in rows]
    # skip empty rows
    rows = [row for row in rows if not (len(row) == 1 and row[0] == "")]

    practitioner = await parse_rows(rows)
    return practitioner


async def main():
    """
    - Go through the output of scraped_doctors_overview.
    - Load page of detailed information about doctors to get specialist information, if any.
    - Also can run assertion checks on the data folder against doctors' described details.
    """
    logger.info(f"Loading doctors jsonfile: {INPUT_JSON_PATH}.")
    with open(INPUT_JSON_PATH, "r") as json_file:
        doctor_data = json.load(json_file)

    logging.info(f"Looping through {len(doctor_data)} doctor records.")
    doctor_urls = [
        DOCTORS_PAGE_FN(doctor["registration_no"])
        for doctor in doctor_data[:3]
    ]

    full_practitioner_list = await load_pages(
        doctor_urls, parse_detailed_doctors_page
    )

    from pprint import pprint

    pprint(full_practitioner_list)

    ## Last part; check against previous version!


if __name__ == "__main__":
    asyncio.run(main())
