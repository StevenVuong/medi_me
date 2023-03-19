import asyncio
import functools
import json
import logging
import random
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from tqdm.asyncio import tqdm

import yaml

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# registered doctors URL; takes page number as parameter
REGISTERED_DOCTORS_URL = (
    lambda x: f"{config_dict['scraper']['doctors_overview']['url']}&page={x}"
)
NUM_PAGES = config_dict["scraper"]["doctors_overview"]["num_pages"]
OUTPUT_JSONFILENAME = config_dict["scraper"]["doctors_overview"]["output_path"]


def retry_with_backoff(retries=5, backoff_in_ms=100):
    """A decorator that retries a function with exponential backoff.

    Args:
        - retries (int): The number of times to retry the function before giving up.
        - backoff_in_ms (int): The initial delay in milliseconds before retrying.

    Returns:
        - callable: A wrapped version of the input function that will be retried with exponential backoff.
    """

    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(*args, **kwargs):
            """Wrapper function that will be retried with exponential backoff."""
            x = 0
            while True:
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    print("Fetch error:", e)

                    if x == retries:
                        raise
                    else:
                        sleep_ms = backoff_in_ms * 2**x + random.uniform(
                            0, 1
                        )
                        await asyncio.sleep(sleep_ms / 1000)
                        x += 1
                        print(f"Retrying {x + 1}/{retries}")

        return wrapped

    return wrapper


@dataclass
class EnZhText:
    """Stores text and can extract both English alphabet and Chinese characters"""

    text: str

    def __init__(self, text: str):
        self.text = text.strip()

    def extract_en(self):
        """Regex that captures alphabet, numbers and basic punctuation .,!?"""
        return " ".join(re.findall(r"[a-zA-Z0-9.,!?]+", self.text))

    def extract_zh(self):
        """
        Note: This is quite crude and only extracts purely
        chinese characters.
        """
        return "".join(re.findall(r"[\u4e00-\u9fff]", self.text))


@dataclass
class Qualification:
    """Class to store qualification of medical practitioner"""

    nature: EnZhText | None  # nature of the qualification
    tag: str | None
    year: int

    def __init__(self, nature_tag: str, year: str):
        """Parse qualification item to class.
        We separate the tag from nature_tag, which is the string inside
        the brackets, and remove the brackets from nature_tag to get nature.
        Args:
            - nature_tag (str): Eg. MB BS (Lond)
            - year (str): year of study
        """
        self.nature = EnZhText(re.sub(r"\[[^]]*\]|\([^)]*\)", "", nature_tag))

        tag = re.findall(r"\[[^]]*\]|\([^)]*\)", nature_tag)
        tag = [match.strip("()") for match in tag]
        self.tag = tag[0] if tag else None

        self.year = int(year)


@dataclass
class Practitioner:
    """Class to store practitioner information, and parse from __init__"""

    registration_no: str
    name: EnZhText
    address: EnZhText
    qualifications: list[Qualification]

    def __init__(self, str_column: list[str]):
        """Format of str_column will be something like:
        ['M15833', '區卓仲AU, CHEUK CHUNG', '', '', '', '香港大學內外全科醫學士MB BS (HK)', '', '2008']
        """
        self.registration_no = str_column[0]
        self.name = EnZhText(str_column[1])
        self.address = EnZhText(str_column[3])
        self.qualifications = [
            Qualification(nature_tag=str_column[5], year=str_column[7])
        ]

    def add_qualifications(self, str_column: list[str]):
        """Format of str_column will be something like:
        ['FHKAM (Radiology)', '', '1999']
        """
        self.qualifications.append(
            Qualification(nature_tag=str_column[0], year=str_column[2])
        )


@retry_with_backoff(retries=5, backoff_in_ms=500)
async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Fetches the content of a web page asynchronously.

    Args:
        - session: An aiohttp.ClientSession object used to make the HTTP request.
        - url: The URL of the web page to fetch.
    Returns:
        The content of the web page as a string if the request is successful,
        otherwise None.
    """
    try:
        async with session.get(url) as response:
            if response.status == 520:
                raise aiohttp.ClientResponseError(f"520 error to: {url}")
            if response.status == 500:
                raise aiohttp.ClientResponseError(f"500 error to: {url}")
            assert (
                response.status == 200
            ), f"Response status: {response.status}"
            return await response.text()
    except aiohttp.ClientConnectionError as e:
        print(f"An error occurred while connecting to {url}: {e}")
    except aiohttp.ClientResponseError as e:
        print(f"An client response error occurred while fetching {url}: {e}")
    except asyncio.TimeoutError as e:
        print(f"A timeout occurred while fetching {url}: {e}")


async def parse_registered_doctors_page(page_request) -> list[Practitioner]:
    """
    Parses registered doctor page url from HK Government list of registered
    medical practitioners.
    Args:
        - page_url(str): URL of page to parse
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

    # after 9th row; as that's when medical doctors' information starts
    for row in rows[9:]:
        # parse individual columns
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]

        # breaks once we get to the bottom of the table
        if cols[0].startswith("« Previous"):
            break

        # parse to Practitioner object; first line is a regiration num 'M17694'
        if cols[0][0] == "M" and len(cols[0]) == 6:
            practitioner = Practitioner(cols)
            practitioner_list.append(practitioner)

        else:
            practitioner_list[-1].add_qualifications(cols)

    return practitioner_list


def save_dataclass_list_to_json(list_to_save: list[Any], output_filepath: str):
    """Takes an input of a dataclass list and saves to json file."""
    with open(output_filepath, "w+", encoding="utf-8") as f:
        json.dump(
            [asdict(obj) for obj in list_to_save],
            f,
            ensure_ascii=False,
            indent=2,
        )


async def load_doctors_pages(
    doctors_fn: Callable[[str], str], num_pages: int
) -> list[Practitioner]:
    """
    Fetches and processes multiple web pages asynchronously.

    Args:
        - doctors_url; Registered doctors url function.
        - num_pages; Number of pages to parse.
    Returns:
        - A list containing the result of processing each page.
    """
    # get page urls
    urls = [doctors_fn(page_num) for page_num in range(num_pages + 1)]
    processed_pages = []

    # load pages async
    async with aiohttp.ClientSession() as session:
        tasks = []
        logger.debug("Fetching URLS")
        for url in tqdm(urls):
            tasks.append(fetch(session, url))
        logger.debug("Gathering Tasks")
        pages = await asyncio.gather(*tasks)
        for page in tqdm(pages):  # add tqdm for progress bar tracking
            if page is not None:
                processed_page = await parse_registered_doctors_page(page)
                processed_pages.extend(processed_page)

    return processed_pages


if __name__ == "__main__":
    # set log level; debug, info, warning, error, critical
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
        level=logging.DEBUG,
    )

    logger.info("Parsing registered doctors page asynchronously.")
    full_practitioner_list = asyncio.run(
        load_doctors_pages(REGISTERED_DOCTORS_URL, NUM_PAGES)
    )

    logger.info(f"Loaded {NUM_PAGES} pages. Saving to {OUTPUT_JSONFILENAME}")
    save_dataclass_list_to_json(full_practitioner_list, OUTPUT_JSONFILENAME)
