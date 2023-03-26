import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")

# https://www.elastic.co/guide/en/elasticsearch/client/python-api/master/connecting.html

# create an elasticsearch index
index_name = "test-index"
index_settings = {
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

    # create index
    es.indices.create(index=index_name, body=index_settings)
    print("Index created successfully!")


if __name__ == "__main__":
    main()
