import os
import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

log = logging.getLogger("azure_helper_functions")
BAD_REQUEST_CODE = (400, None)

def init_connection(container_name):
    if (os.environ.get("AZURE_STORAGE_CONNECTION_STRING") is not None):
        connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    else:
        log.error(f"'AZURE_STORAGE_CONNECTION_STRING' environment variable not set.")
        return BAD_REQUEST_CODE
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)
    except ConnectionError as err:
        log.error(f"'AZURE_STORAGE_CONNECTION_STRING' environment variable not set. {err}")
        return BAD_REQUEST_CODE
    return blob_service_client, container_client

def get_blobs_from_container(container_client):
    return container_client.list_blobs()

def get_blobs_from_container_path(container_client, path_to_dir):
    filtered_list = list(filter(lambda blob: blob.name.startswith(path_to_dir), container_client.list_blobs()))
    return filtered_list