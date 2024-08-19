from __future__ import unicode_literals
import logging

logger = logging.getLogger('openerp.' + __name__)


def get_azure_blob_client():
    from azure.storage.blob import BlobServiceClient
    from tools.config import config
    connection_string = config.get('azure_connection_string')
    if not connection_string:
        raise ValueError('Missing Azure Blob Storage configuration')
    client = BlobServiceClient.from_connection_string(connection_string)
    return client


def get_object(client, container_name, object_path):
    container_client = client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(object_path)
    downloader = blob_client.download_blob()
    return downloader.readall()
