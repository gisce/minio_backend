from __future__ import absolute_import
from osv import fields
from tools import human_size
import base64
from io import BytesIO
from .azure_backend import get_azure_blob_client
import magic
from slugify import slugify


class AzureBlobFile(fields.text):
    """Azure Blob Storage storing file in Azure
    """
    _classic_read = False
    _classic_write = False
    pg_type = 'text', 'text'

    def __init__(self, string, container_name, subfolder='', **args):
        self.container_name = slugify(container_name)
        self.subfolder = subfolder
        super(AzureBlobFile, self).__init__(
            string=string, widget='binary', **args
        )

    def get_oids(self, cursor, obj, ids, name):
        cursor.execute(
            "select id, " + name + " from " + obj._table + " where id  in %s", (tuple(ids), )
        )
        res = dict([(x[0], x[1]) for x in cursor.fetchall()])
        return res

    def get_filename(self, obj, rid, name, context=None):
        if context is None:
            context = {}
        subfolder = context.get('subfolder', self.subfolder)
        if subfolder:
            return '{}/{}/{}_{}'.format(
                obj._table, subfolder, rid, name)
        return '{}/{}_{}'.format(obj._table, rid, name)

    def set(self, cursor, obj, rid, name, value, user=None, context=None):
        if context is None:
            context = {}
        client = get_azure_blob_client()
        container_client = client.get_container_client(self.container_name)
        if not container_client.exists():
            container_client.create_container()
        for rid, oid in self.get_oids(cursor, obj, [rid], name).items():
            if not value and oid:
                container_client.delete_blob(oid)
                value = None
            elif value:
                key = '{}_filename'.format(name)
                ctx_filename = context.get(key)
                if oid:
                    filename = oid
                    if ctx_filename:
                        if oid != ctx_filename:
                            container_client.delete_blob(oid)
                        filename = self.get_filename(
                            obj, rid, ctx_filename, context=context)
                else:
                    if ctx_filename:
                        filename = self.get_filename(
                            obj, rid, ctx_filename, context=context)
                    else:
                        filename = self.get_filename(
                            obj, rid, name, context=context)

                content = base64.b64decode(value)
                content_type = magic.from_buffer(content, mime=True)
                container_client.upload_blob(
                    name=filename, data=BytesIO(content), blob_type="BlockBlob", content_type=content_type, overwrite=True
                )
                value = filename
            return super(AzureBlobFile, self).set(
                cursor, obj, rid, name, value, user, context
            )

    def get(self, cursor, obj, ids, name, user=None, offset=0, context=None,
            values=None):
        if context is None:
            context = {}
        client = get_azure_blob_client()
        container_client = client.get_container_client(self.container_name)
        if not container_client.exists():
            container_client.create_container()
        res = self.get_oids(cursor, obj, ids, name)
        for rid, oid in res.items():
            if oid:
                oid = oid
                blob_client = container_client.get_blob_client(oid)
                downloader = blob_client.download_blob()
                val = downloader.readall()
                if context.get('bin_size', False) and val:
                    res[rid] = '%s' % human_size(val)
                else:
                    res[rid] = base64.b64encode(val)
            else:
                res[rid] = False
        return res
