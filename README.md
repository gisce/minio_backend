# Minio Storage server

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