import logging

logger = logging.getLogger('openerp.' + __name__)


def get_minio_client():
    from minio import Minio
    from tools.config import config
    endpoint = config.get('minio_endpoint')
    access_key = config.get('minio_access_key')
    secret_key = config.get('minio_secret_key')
    secure = config.get('minio_secure', False)
    if not (endpoint and access_key and secret_key):
        raise ValueError('Missing Minio Server configuration')
    if not secure:
        logger.warning('Using an insecure connection to Minio server.')
    client = Minio(
        endpoint, access_key=access_key, secret_key=secret_key, secure=secure
    )
    return client
