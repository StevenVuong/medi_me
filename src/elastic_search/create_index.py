import logging
import os

import yaml
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from loguru import logger

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
)
logger.add(config_dict["logpath"])


def create_elasticsearch_client(
    host: str,
    certs_path: str,
    username: str,
    password: str,
) -> Elasticsearch:
    """Creates an instance of the Elasticsearch client.

    This function creates an instance of the Elasticsearch client with the specified host,
    certificate path, username, and password. It checks if the client info is not None
    and returns the client instance.

    Args:
        host (str): The host of the Elasticsearch cluster.
        certs_path (str): The path to the certificate file.
        username (str): The username for basic authentication.
        password (str): The password for basic authentication.

    Returns:
        Elasticsearch: An instance of the Elasticsearch client.
    """
    # Create the client instance
    es = Elasticsearch(
        host,
        ca_certs=certs_path,
        basic_auth=(username, password),
    )

    # Successful response!
    client_info = es.info()
    assert client_info is not None, "Elasticsearch client info is None!"

    return es


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
