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
