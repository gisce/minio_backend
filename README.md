# Minio Storage server

[![Minio Backend Tests](https://github.com/gisce/minio_backend/actions/workflows/minio_tests.yml/badge.svg)](https://github.com/gisce/minio_backend/actions/workflows/minio_tests.yml)

Store files into a [Minio Server](https://min.io/) which is a Amazon S3 Open Source alternative.

## Define binary columns

```python
from osv import osv, fields
from minio_backend.fields import S3File

class ExampleObject(osv.osv):
    _name = 'example.object'
    _columns = {
        'name': fields.char('Name', size=64),
        'file': S3File('File', 'test')
    }

    
ExampleObject()
```

## API

`class S3File(string, bucket)`:

# Azure Blob Storage

[![Azure Backend Tests](https://github.com/gisce/minio_backend/actions/workflows/azure_tests.yml/badge.svg)](https://github.com/gisce/minio_backend/actions/workflows/azure_tests.yml)

Store files into an [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/) which is a highly scalable object storage solution from Microsoft.

## Define binary columns

```python
from osv import osv, fields
from azure_backend.fields import AzureBlobFile

class ExampleObject(osv.osv):
    _name = 'example.object'
    _columns = {
        'name': fields.char('Name', size=64),
        'file': AzureBlobFile('File', 'test')
    }

ExampleObject()
```

## API

`class AzureBlobFile(string, container_name)`
