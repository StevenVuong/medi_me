from elasticsearch import Elasticsearch


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
