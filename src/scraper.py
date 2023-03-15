import requests
from bs4 import BeautifulSoup
from prefect import flow, task
import re
from dataclasses import dataclass


REGISTERED_DOCTORS_URL = "https://www.mchk.org.hk/english/list_register/list.php?page=1&ipp=20&type=L"


@dataclass
class EnZhText:
    text: str

    def __init__(self, text: str):
        self.text = text.strip()

    def extract_en(self):
        return " ".join(re.findall(r"[a-zA-Z0-9.,!?]+", self.text))

    def extract_zh(self):
        # Note: This is quite crude and only extracts purely
        # chinese characters. Does not capture nuances.
        return "".join(re.findall(r"[\u4e00-\u9fff]", self.text))


@dataclass
class Qualification:
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

        # breaks once we get to the bottom of the table
        if cols[0].startswith("« Previous"):
            break

        # parse to Practitioner object
        if cols[0][0] == "M":
            practitioner = Practitioner(cols)
            practitioner_list.append(practitioner)

        else:
            practitioner_list[-1].add_qualifications(cols)

    for p in practitioner_list:
        if p.address.text != "":
            print(p)
            print(p.address.extract_en())
            print(p.address.extract_zh())


if __name__ == "__main__":
    main()
