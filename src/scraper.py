from bs4 import BeautifulSoup
import requests

if __name__ == "__main__":
    URL = "https://www.mchk.org.hk/english/list_register/list.php?type=L"
    page_request = requests.get(URL)

    soup = BeautifulSoup(
        page_request.content, "lxml"
    )  # If this line causes an error, run 'pip install html5lib' or install html5lib

    table = soup.find_all("table")[0]
    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        print(cols)
