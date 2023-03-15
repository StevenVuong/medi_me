import requests
from bs4 import BeautifulSoup
from prefect import flow, task
import re
from pydantic import BaseModel, ValidationError, validator


REGISTERED_DOCTORS_URL = "https://www.mchk.org.hk/english/list_register/list.php?page=1&ipp=20&type=L"


class EnZhText(BaseModel):
    text: str

    def extract_en(self):
        return " ".join(re.findall(r"[a-zA-Z0-9.,!?]+", self.text))

    def extract_zh(self):
        return " ".join(re.findall(r"[\\u4e00-\\u9fff0-9.,!?]+", self.text))


class Qualification(BaseModel):
    nature: EnZhText
    year: int
    tag: str | None

    def __init__(self, nature_tag:str, year:str):
        self.nature = 
        self.tag = 
        self.year = int(year)


class Practitioner(BaseModel):
    registration_no: str
    name: EnZhText
    address: EnZhText
    qualifications: list[Qualification]


@task
def make_request(url: str) -> requests.Response:
    """
    Send a GET request to a given URL and return the response object.

    Parameters:
        - url (str): The URL to send the request to.

    Returns:
        - requests.Response: The response object from the server.

    Raises:
        - requests.exceptions.RequestException: If the request fails for any reason.
        - Exception: If any other error occurs during the process.
    """
    try:
        response = requests.get(url)
        print(response.status_code)
        return response

    except requests.exceptions.RequestException as e:
        print(f"Request to {url} was unsuccessful! Error code: {e}")

    except Exception as e:
        print(f"Error when trying to parse {url}! Error code: {e}")


@flow
def main():
    # make request and initialise beautiful soup object
    page_request = make_request(REGISTERED_DOCTORS_URL)
    soup = BeautifulSoup(page_request.content, "lxml")

    # find the first table on the page
    table = soup.find_all("table")[0]
    rows = table.find_all("tr")

    # initialise practitioner list to parse
    practitioner_list = []

    # after 9th row; as that's when medical doctors' information starts
    for row in rows[9:]:
        # parse individual columns
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        cols = [ele for ele in cols if ele]

        # parse to Practitioner object
        if cols[0][0]=='M':

            # todo; move logic to practitioner
            practitioner_list.append(Practitioner(
                registration_no = cols[0]
                name = cols[1]
                address = cols[2]
                qualifications = [Qualification(nature=cols[3])]
            ))
        else:
            practitioner_list.append()



        # breaks once we get to the bottom of the table
        if cols[0].startswith("« Previous"):
            break

        print(cols)


if __name__ == "__main__":
    main()
