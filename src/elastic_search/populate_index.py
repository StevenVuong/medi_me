import json
import logging
import os

import yaml
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from loguru import logger
from tqdm import tqdm
from utils import create_elasticsearch_client

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# load environment variables and set constants
load_dotenv()
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
INDEX_NAME = os.getenv("ELASTIC_INDEXNAME")
CERTS_PATH = config_dict["elasticsearch"]["certs_path"]
HOST = config_dict["elasticsearch"]["host_path"]
DATA_DIR = config_dict["scraper"]["datapath"]

# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
    filename=config_dict["logpath"],
)


def load_and_index_json_files(
    json_filepaths: str,
    index_name: str,
    data_dir: str,
    es_client: Elasticsearch,
):
    """Loads and indexes JSON files into an Elasticsearch index.

    Args:
        json_filepaths (str): The file paths of the JSON files to be indexed.
        index_name (str): The name of the Elasticsearch index.
        data_dir (str): The directory where the JSON files are located.
        es_client (Elasticsearch): The Elasticsearch client instance.

    """
    # add data to index
    for jf in tqdm(json_filepaths):
        with open(data_dir + jf) as raw_data:
            json_docs = json.load(raw_data)

        # add each json doc to the index
        for json_doc in tqdm(json_docs):
            es_client.index(index=index_name, document=json_doc)


if __name__ == "__main__":
    logging.info("Creating elasticsearch client")
    es_client = create_elasticsearch_client(
        host=HOST,
        certs_path=CERTS_PATH,
        username=ELASTIC_USERNAME,
        password=ELASTIC_PASSWORD,
    )

    # check if index exists
    index_exists = es_client.indices.exists(index=INDEX_NAME)
    assert index_exists, f"{INDEX_NAME} Index does not exist!"
    logging.info("Index exists! Proceeding to add data..")

    # load json files
    json_filepaths = [
        f
        for f in os.listdir(DATA_DIR)
        if f.endswith("_scraped_doctors_detail.json")
    ]

    load_and_index_json_files(
        json_filepaths=json_filepaths,
        index_name=INDEX_NAME,
        data_dir=DATA_DIR,
        es_client=es_client,
    )

    # Refresh the index
    es_client.indices.refresh(index=INDEX_NAME)

    # Get the document count
    res = es_client.cat.count(index=INDEX_NAME, params={"format": "json"})
    count = int(res[0]["count"])
    logging.info(f"{count} number of documents added to index!")
