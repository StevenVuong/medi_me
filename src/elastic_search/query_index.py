import logging
import os
from elasticsearch import Elasticsearch
from elastic_transport import ObjectApiResponse
import yaml
from dotenv import load_dotenv
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


# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
    filename=config_dict["logpath"],
)


def search(
    es_client: Elasticsearch, index_name: str, query_string: dict
) -> ObjectApiResponse:
    """Searches the index for the query.
    Args:
        es_client: Elasticsearch client
        index_name: Name of the index to search
        query: Query to search for
    Returns:
        res: Elasticsearch response
    """
    # Search query
    query = {
        "multi_match": {
            "query": query_string,
            "fields": [
                "name",
                "address",
                "qualifications.nature.text",
                "qualifications.nature.tag",
                "specialty_name",
                "speciality_qualification.nature.text",
                "speciality_qualification.nature.tag",
            ],
        }
    }

    # get results from elasticsearch; ordered by score in descending order
    res = es_client.search(index=index_name, query=query)
    return res


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
    logging.info("Index exists!")

    # Refresh the index
    es_client.indices.refresh(index=INDEX_NAME)

    # Get the document count
    res = es_client.cat.count(index=INDEX_NAME, format="json")
    count = int(res[0]["count"])
    logging.info(f"Document count: {count}")

    # Search for a query
    query_string = "Dr. John"
    logging.info(f"Searching {INDEX_NAME} index for {query_string}...")
    res = search(es_client, INDEX_NAME, query_string)
    logging.info(f"{res['hits']['total']['value']} results found")

    # printing hits
    for hit in res["hits"]["hits"]:
        print(hit["_score"])
        print(hit["_source"])
