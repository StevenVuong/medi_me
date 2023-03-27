import asyncio
import json
import logging
import os
from typing import IO

import yaml
from bs4 import BeautifulSoup
from dr_dataclass import Practitioner, Qualification
from tqdm.asyncio import tqdm
from util import load_pages, save_dataclass_list_to_json

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# detailed registered doctors url; takes registration number as parameter.
DOCTORS_PAGE_FN = (
    lambda x: f"{config_dict['scraper']['doctors_detail']['url']}{x}"
)
INPUT_JSON_PATH = config_dict["scraper"]["doctors_overview"]["output_path"]
OUTPUT_JSON_PATH = config_dict["scraper"]["doctors_detail"]["output_path"]
BATCH_SIZE = config_dict["scraper"]["doctors_detail"]["batch_size"]

# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
    filename=config_dict["logpath"],
)


async def parse_rows(rows: list[list[str]]) -> list[Practitioner]:
    """
    Takes in a list of rows containing doctor information and returns a Practitioner object.

    Args:
        - rows (list[list[str]]): A list of lists where each inner list represents
          a row of practitioner information.
    Returns:
        - list[Practitioner]: Containing the parsed information from the input rows.
    """
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
                # set address to blank if is just a '-' value
                address = "" if cols[-1] == "-" else cols[-1]
                practitoner_info["address"] = address

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

            # to add to qualifications; append
            case "":
                if "speciality_qualification" in practitoner_info:
                    practitoner_info["qualifications"].append(
                        Qualification(nature_tag=cols[-2], year=cols[-1])
                    )
                    raise KeyError("Multiple specializations!!")
                elif "qualifications" in practitoner_info:
                    practitoner_info["qualifications"].append(
                        Qualification(nature_tag=cols[-2], year=cols[-1])
                    )
                    continue
                raise KeyError(f"qualifications not in {practitoner_info}!")

    return [Practitioner(**practitoner_info)]  # return list to extend


async def parse_detailed_doctors_page(page_request: IO[str]) -> Practitioner:
    """
    Takes in a page request and returns a Practitioner object.
    Uses BeautifulSoup to parse HTML content and extract information from first
    table found on the page. Returns a Practitioner object afterward.

    Args:
        - page_request: A string representing an HTML page request
    Returns:
        - A Practitioner object containing information extracted from the page
    """
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
    logging.info(f"Loading doctors jsonfile: {INPUT_JSON_PATH}.")
    with open(INPUT_JSON_PATH, "r") as json_file:
        doctor_data = json.load(json_file)

    logging.info(f"Loading {len(doctor_data)} doctor records.")
    # >15,000 doctors urls; split into batches otherwise error 1015
    doctor_urls = [
        DOCTORS_PAGE_FN(doctor["registration_no"]) for doctor in doctor_data
    ]

    # split save filepath
    file_name, file_ext = os.path.split(OUTPUT_JSON_PATH)

    # loop thorugh batches
    for i in range(0, len(doctor_urls), BATCH_SIZE):
        doctors_url_batch = doctor_urls[i : i + BATCH_SIZE]
        logging.info(f"Handling batch {i}:{i+BATCH_SIZE}")

        full_practitioner_list = await load_pages(
            doctors_url_batch, parse_detailed_doctors_page
        )
        logging.info("Doctor records loaded!")

        logging.info("Verifying new detailed records against overview..")
        for old_dd, new_dd in tqdm(
            zip(doctor_data[i : i + BATCH_SIZE], full_practitioner_list)
        ):
            assert old_dd["registration_no"] == new_dd.registration_no
            assert old_dd["name"]["text"] == new_dd.name
            assert old_dd["address"]["text"] == new_dd.address

        save_filepath = file_name + f"/{i}_" + file_ext
        logging.info(f"Saving to file: {save_filepath}")
        save_dataclass_list_to_json(full_practitioner_list, save_filepath)


if __name__ == "__main__":
    asyncio.run(main())
