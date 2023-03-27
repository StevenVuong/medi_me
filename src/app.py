import streamlit as st
import logging
import os

import yaml
from dotenv import load_dotenv
from elastic_search.utils import create_elasticsearch_client
from elastic_search.query_index import search

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

logging.info("Creating elasticsearch client")
es_client = create_elasticsearch_client(
    host=HOST,
    certs_path=CERTS_PATH,
    username=ELASTIC_USERNAME,
    password=ELASTIC_PASSWORD,
)


def st_hit(hit):
    st.write(f"Registration No: {hit['registration_no']}")
    st.write(f"Name: {hit['name']}")
    st.write(f"Address: {hit['address']}")

    st.write("Qualifications:")
    for qual in hit["qualifications"]:
        st.write(f"{qual['nature']['text']} ({qual['tag']}) - {qual['year']}")

    st.write(f"Specialty Registration No: {hit['specialty_registration_no']}")
    st.write(f"Specialty Name: {hit['specialty_name']}")
    st.write(f"Speciality Qualification: {hit['speciality_qualification']}")


def main():
    st.title("Search Doctor's Register:")
    search_query = st.text_input("Enter search words:")

    # check if index exists
    index_exists = es_client.indices.exists(index=INDEX_NAME)
    assert index_exists, f"{INDEX_NAME} Index does not exist!"
    logging.info("Index exists! Proceeding with query.")

    # Refresh the index
    es_client.indices.refresh(index=INDEX_NAME)

    # TODO: Format and make look pretty
    # https://betterprogramming.pub/build-a-search-engine-for-medium-stories-using-streamlit-and-elasticsearch-b6e717819448
    if search_query:
        # Search query
        logging.info(f"Searching {INDEX_NAME} index for {search_query}...")
        res = search(es_client, INDEX_NAME, search_query)
        logging.info(f"{res['hits']['total']['value']} results found")

        for hit in res["hits"]["hits"]:
            print(hit)
            st_hit(hit["_source"])
            st.write("-------------------")


if __name__ == "__main__":
    main()
