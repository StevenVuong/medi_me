import asyncio
import functools
import json
import logging
import random
from dataclasses import asdict
from typing import IO, Any, Callable

import aiohttp
import yaml
from loguru import logger
from tqdm.asyncio import tqdm

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
)
logger.add(config_dict["logpath"])


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
                        if x == retries + 1:
                            raise asyncio.ClientResponseError(
                                f"Failed after {retries} attempts!"
                            )
                        print(f"Retrying {x + 1}/{retries}")

        return wrapped

    return wrapper


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
            if response.status == 429:  # too many requests
                asyncio.sleep(1)  # sleep for 1 second
                raise aiohttp.ClientResponseError(f"429 error to: {url}")
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


def save_dataclass_list_to_json(list_to_save: list[Any], output_filepath: str):
    """Takes an input of a dataclass list and saves to json file."""
    with open(output_filepath, "w+", encoding="utf-8") as f:
        json.dump(
            [asdict(obj) for obj in list_to_save],
            f,
            ensure_ascii=False,
            indent=2,
        )


async def load_pages(
    urls_to_parse: list[str], parsing_fn: Callable[[IO[str]], list[Any]]
) -> list[Any]:
    """
    Fetches and processes multiple web pages asynchronously.

    Args:
        - urls_to_parse; urls to load and parse
    Returns:
        - A list containing the result of processing each page.
    """
    processed_pages = []
    connector = aiohttp.TCPConnector(limit=50)  # simultaneous connections

    # load pages async
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        logger.debug("Fetching URLS")
        for url in tqdm(urls_to_parse):
            tasks.append(fetch(session, url))

        logger.debug("Gathering Tasks")
        pages = await asyncio.gather(*tasks)
        for page in tqdm(pages):
            if page is None:
                continue

            processed_page = await parsing_fn(page)

            if processed_page is None:
                continue

            assert type(processed_page) == list
            processed_pages.extend(processed_page)

    return processed_pages
