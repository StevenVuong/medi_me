import json
import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from tqdm import tqdm

load_dotenv()
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
INDEX_NAME = os.getenv("ELASTIC_INDEXNAME")
data_filepath = "./data/"


def main():
    # Create the client instance
    es = Elasticsearch(
        "https://localhost:9200",
        ca_certs="./http_ca.crt",
        basic_auth=("elastic", ELASTIC_PASSWORD),
    )

    # Successful response!
    client_info = es.info()
    print("Elasticsearch client info:")
    print(client_info)

    # check if index exists
    index_exists = es.indices.exists(index=INDEX_NAME)
    assert index_exists, f"{INDEX_NAME} Index does not exist!"

    # load json files
    json_files_to_load = os.listdir(data_filepath)
    json_files_to_load = [
        f
        for f in json_files_to_load
        if f.endswith("_scraped_doctors_detail.json")
    ]

    # add data to index
    for jf in tqdm(json_files_to_load):
        with open(data_filepath + jf) as raw_data:
            json_docs = json.load(raw_data)

        # add each json doc to the index
        for json_doc in tqdm(json_docs):
            es.index(index=INDEX_NAME, document=json_doc)


if __name__ == "__main__":
    main()
