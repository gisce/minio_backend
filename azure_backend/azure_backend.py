from __future__ import unicode_literals
import logging

logger = logging.getLogger('openerp.' + __name__)
logging.getLogger(
    'azure.core.pipeline.policies.http_logging_policy'
).setLevel(logging.WARNING)

VALID_MODES = {'connection_string', 'sas_token', 'app_registration'}


def get_azure_blob_client():
    from tools.config import config
    mode = config.get('azure_auth_mode', 'connection_string')
    assert mode in VALID_MODES

    if mode in ('connection_string', 'sas_token'):
        connection_string = config.get('azure_connection_string')
        if not connection_string:
            raise ValueError('Missing Azure Blob Storage configuration')

        if mode == 'connection_string':
            return get_azure_blob_client_from_connection_string(connection_string)
        elif mode == 'sas_token':
            return get_azure_blob_client_from_sas_token(connection_string)

        raise NotImplementedError

    elif mode == 'app_registration':
        tenant_id = config.get('azure_connection_tenant_id')
        client_id = config.get('azure_connection_client_id')
        client_secret = config.get('azure_connection_client_secret')
        account_url = config.get('azure_connection_account_url')
        return get_azure_blob_client_from_app_registration(
            tenant_id, client_id, client_secret, account_url
        )
    raise NotImplementedError


def get_azure_blob_client_from_connection_string(connection_string):
    from azure.storage.blob import BlobServiceClient
    client = BlobServiceClient.from_connection_string(connection_string)
    return client

def get_azure_blob_client_from_sas_token(sas_token):
    from azure.storage.blob import BlobServiceClient
    client = BlobServiceClient(sas_token)
    return client

def get_azure_blob_client_from_app_registration(tenant_id, client_id, client_secret, account_url):
    from azure.identity import ClientSecretCredential
    from azure.storage.blob import BlobServiceClient
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    client = BlobServiceClient(
        account_url=account_url,
        credential=credential
    )
    return client

def get_object(client, container_name, object_path):
    container_client = client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(object_path)
    downloader = blob_client.download_blob()
    return downloader.readall()
