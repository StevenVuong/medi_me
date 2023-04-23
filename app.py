import logging
import os
import re

import openai
import streamlit as st
import yaml
from dotenv import load_dotenv

from src.elastic_search.query_index import search
from src.elastic_search.utils import create_elasticsearch_client
from src.openai_query import call_openai, strip_string

with open("./config.yaml") as f:
    config_dict = yaml.safe_load(f)

# load environment variables
load_dotenv()

# load values for Elasticsearch
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
INDEX_NAME = os.getenv("ELASTIC_INDEXNAME")
CERTS_PATH = config_dict["elasticsearch"]["certs_path"]
HOST = config_dict["elasticsearch"]["host_path"]

# load values for OpenAPI
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")


# set log level; debug, info, warning, error, critical
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
    level=logging.DEBUG,
    filename=config_dict["logpath"],
)

logging.info("Creating elasticsearch client")
ES_CLIENT = create_elasticsearch_client(
    host=HOST,
    certs_path=CERTS_PATH,
    username=ELASTIC_USERNAME,
    password=ELASTIC_PASSWORD,
)

MEDICAL_PROMPT = (
    "Suggest medical specialists for a patient to see based on "
    "their described symptoms in the format of {{specialist 1}},"
    " {{specialist 2}}, ..., {{specialist n}}.\nPatient:"
)
MEDICAL_PROMPT_DESC = "Explain very very simply what the specialist does:"


def st_hit(hit):
    """Displays the details of a hit from Elasticsearch medical database in
    Streamlit format.

    Args:
        hit (dict): A dictionary containing the details of a hit.

    Returns:
        None
    """
    st.write(
        f"**Name:** {hit['name']}, Registration No: {hit['registration_no']}"
    )
    st.write(f"**Address:** {hit['address']}")

    st.write("**Qualifications:**")
    for qual in hit["qualifications"]:
        st.write(f"{qual['nature']['text']} ({qual['tag']}) - {qual['year']}")

    if hit["specialty_registration_no"]:
        st.write(
            f"**Specialty Name:** {hit['specialty_name']}, Registration No: {hit['specialty_registration_no']}"
        )
        st.write("**Specialty Qualifications:**")
        if hit["speciality_qualification"]:
            qual = hit["speciality_qualification"]
            st.write(
                f"{qual['nature']['text']}:({qual['tag']}) - {qual['year']}"
            )


def display_doctors_register(search_query: str):
    """Searches for doctors in an Elasticsearch index and displays the results
    of doctor's register and parses the result to be displayed on Streamlit.

    This function checks if the Elasticsearch index exists and refreshes it
    before performing a search query. The search results are then displayed.

    Args:
        search_query (str): Search query  when searching for doctors in Elasticsearch index.

    Raises:
        AssertionError: If the Elasticsearch index does not exist.
    """
    # check if index exists
    index_exists = ES_CLIENT.indices.exists(index=INDEX_NAME)
    assert index_exists, f"{INDEX_NAME} Index does not exist!"
    logging.info("Index exists! Proceeding with query.")

    # Refresh the index
    ES_CLIENT.indices.refresh(index=INDEX_NAME)

    if search_query:
        # Search query
        logging.info(f"Searching {INDEX_NAME} index for {search_query}...")
        res = search(ES_CLIENT, INDEX_NAME, search_query)
        logging.info(f"{res['hits']['total']['value']} results found")
        logging.info(res)

        for hit in res["hits"]["hits"]:
            st_hit(hit["_source"])
            st.write("-------------------")


def display_medical_issue(search_query: str):
    """
    Queries OpenAI's API for medical specialists related to medical problem and
    displays the results for user to select. Then queries again for a
    description of the specialist. Returns medical specialist chosen.

    Args:
        search_query (str): The medical issue to search for.

    Returns:
        str: The selected medical specialist.
    """
    # create a prompt for the user to enter their medical problem
    prompt = MEDICAL_PROMPT + search_query
    logging.info(f"Querying OpenAPI: {prompt}.")

    # get the response from OpenAI's API
    query_response = call_openai(prompt)
    logging.info(f"OpenAPI response: {query_response}.")

    # parse specialist names from the response
    medical_specialists = re.findall(r"{{(.*?)}}", query_response)
    st.write(
        f"Found {len(medical_specialists)} medical specialists related to your search."
    )
    medical_specialist_option = st.selectbox(
        "Select options:", medical_specialists
    )
    logging.info(f"Selected specialist: {medical_specialist_option}.")

    # get special description
    specialist_description = call_openai(
        MEDICAL_PROMPT_DESC + medical_specialist_option
    )
    st.write(specialist_description)
    logging.info(f"Specialist description: {specialist_description}.")
    st.write("---")
    return medical_specialist_option


def main():
    """Displays a search bar and searches for the query in Elasticsearch index.

    Raises:
        AssertionError: If the Elasticsearch index does not exist.
    """
    query_option = st.radio(
        "Search by:", ["Doctor's Register", "Medical Issue"], index=0
    )

    if query_option == "Doctor's Register":
        search_query = st.text_input(
            "Enter the medical specialist you want to search:"
        )
        logging.info(f"{query_option} Query: {search_query}.")
        display_doctors_register(search_query)

    if query_option == "Medical Issue":
        search_query = st.text_input("Enter your medical issue:")
        logging.info(f"{query_option} Query: {search_query}.")
        medical_specialist_option = display_medical_issue(search_query)
        display_doctors_register(medical_specialist_option)

    st.write(
        "Disclaimer: This is a prototype and not a medical too. Please consult a"
        "doctor for any medical advice and/or the emergency room for any medical"
        "emergencies."
    )


if __name__ == "__main__":
    main()
