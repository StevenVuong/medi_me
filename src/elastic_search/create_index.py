import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
INDEX_NAME = os.getenv("ELASTIC_INDEXNAME")

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


def create_elasticsearch_client(
    host: str = "https://localhost:9200",
    certs_path: str = "./http_ca.crt",
    username: str = "elastic",
    password: str = ELASTIC_PASSWORD,
) -> Elasticsearch:
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
    # create index
    es_client.indices.create(index=index_name, body=index_settings)

    # check if index exists
    index_exists = es_client.indices.exists(index=index_name)
    assert index_exists, f"{index_name} Index does not exist!"
    print("Index created successfully!")


if __name__ == "__main__":
    es_client = create_elasticsearch_client()
    create_index(es_client, INDEX_NAME, INDEX_SETTINGS)
