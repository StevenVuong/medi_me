import streamlit as st
import logging
import os

import yaml
from dotenv import load_dotenv
from loguru import logger
from elastic_search.utils import create_elasticsearch_client

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


def main():
    st.title("Search Doctor's Register:")
    search = st.text_input("Enter search words:")


if __name__ == "__main__":
    main()
