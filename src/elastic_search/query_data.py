import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")

# create an elasticsearch index
index_name = "test-index"

# Create the client instance
es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="./http_ca.crt",
    basic_auth=("elastic", ELASTIC_PASSWORD),
)

res = es.search(index=index_name, body={"query": {"match_all": {}}})

print("Got %d Hits:" % res["hits"]["total"]["value"])
for hit in res["hits"]["hits"]:
    print(hit["_source"])
