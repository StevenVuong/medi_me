import asyncio
import functools
import json
import random
from dataclasses import asdict
from typing import Any

import aiohttp


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


def save_dataclass_list_to_json(list_to_save: list[Any], output_filepath: str):
    """Takes an input of a dataclass list and saves to json file."""
    with open(output_filepath, "w+", encoding="utf-8") as f:
        json.dump(
            [asdict(obj) for obj in list_to_save],
            f,
            ensure_ascii=False,
            indent=2,
        )
