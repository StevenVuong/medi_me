import logging
import os

import yaml
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
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

# based off of scraped doctors data
INDEX_SETTINGS = {
    "mappings": {
        "properties": {
            "registration_no": {"type": "keyword"},
            "name": {"type": "text"},
            "address": {"type": "text"},
            "qualifications": {
                "properties": {
                    "nature": {"properties": {"text": {"type": "text"}}},
                    "tag": {"type": "keyword"},
                    "year": {"type": "integer"},
                }
            },
            "specialty_registration_no": {"type": "keyword"},
            "specialty_name": {"type": "text"},
            "speciality_qualification": {
                "properties": {
                    "nature": {"properties": {"text": {"type": "text"}}},
                    "tag": {"type": "keyword"},
                    "year": {"type": "integer"},
                }
            },
        }
    }
}

# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
    filename=config_dict["logpath"],
)


def create_index(
    es_client: Elasticsearch, index_name: str, index_settings: dict
):
    """Creates an index in Elasticsearch.

    This function creates an index with the specified name and settings using the provided
    Elasticsearch client instance. It checks if the index exists and prints a success message
    if the index was created successfully.

    Args:
        es_client (Elasticsearch): An instance of the Elasticsearch client.
        index_name (str): The name of the index to create.
        index_settings (dict): The settings for the index.

    """
    if not es_client.indices.exists():
        # create index
        es_client.indices.create(index=index_name, body=index_settings)

    # check if index exists
    index_exists = es_client.indices.exists(index=index_name)
    assert index_exists, f"{index_name} Index does not exist!"
    print("Index created successfully!")


if __name__ == "__main__":
    logging.info("Creating elasticsearch client")
    es_client = create_elasticsearch_client(
        host=HOST,
        certs_path=CERTS_PATH,
        username=ELASTIC_USERNAME,
        password=ELASTIC_PASSWORD,
    )
    logging.info(f"Creating index {INDEX_NAME}")
    create_index(es_client, INDEX_NAME, INDEX_SETTINGS)
