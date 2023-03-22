from elasticsearch import Elasticsearch
import configparser

config = configparser.ConfigParser()
config.read("./.secrets/config.ini")

print(config["ELASTIC"])
# Create the client instance
client = Elasticsearch(
    "https://localhost:9200",
    ca_certs="./.secrets/http_ca.crt",
    basic_auth=("elastic", config["ELASTIC"]["PASSWORD"]),
)

# Successful response!
client_info = client.info()
print(client_info)
# {'name': 'instance-0000000000', 'cluster_name': ...}
