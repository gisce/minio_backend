from __future__ import absolute_import
from osv import fields
from tools import human_size
import base64
from io import BytesIO
from .minio_backend import get_minio_client
import magic


class S3File(fields.text):
    """S3 filesystem storing file in Minio (S3 compatible server)
    """
    _classic_read = False
    _classic_write = False
    pg_type = 'text', 'text'

    def __init__(self, string, bucket, **args):
        self.bucket = bucket
        super(S3File, self).__init__(
            string=string, widget='binary', **args
        )

    def get_oids(self, cursor, obj, ids, name):
        cursor.execute("select id, " + name + " from " + obj._table +
                       " where id  in %s", (tuple(ids), ))
        res = dict([(x[0], x[1]) for x in cursor.fetchall()])
        return res

    def get_filename(self, obj, rid, name, context=None):
        if context is None:
            context = {}
        if context.get('subfolder'):
            return '{}/{}/{}_{}'.format(
                obj._table, context['subfolder'], rid, name)
        return '{}/{}_{}'.format(obj._table, rid, name)

    def set(self, cursor, obj, rid, name, value, user=None, context=None):
        if context is None:
            context = {}
        client = get_minio_client()
        if not client.bucket_exists(self.bucket):
            client.make_bucket(self.bucket)
        for rid, oid in self.get_oids(cursor, obj, [rid], name).items():
            if not value and oid:
                client.remove_object(self.bucket, oid)
                value = None
            elif value:
                key = '{}_filename'.format(name)
                ctx_filename = context.get(key)
                if oid:
                    filename = oid
                    if ctx_filename:
                        if oid != ctx_filename:
                            client.remove_object(self.bucket, oid)
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
                length = len(content)
                content_type = magic.from_buffer(content, mime=True)
                content = BytesIO(content)
                client.put_object(
                    self.bucket, filename, content, length=length,
                    content_type=content_type
                )
                value = filename
            return super(S3File, self).set(
                cursor, obj, rid, name, value, user, context
            )

    def get(self, cursor, obj, ids, name, user=None, offset=0, context=None,
            values=None):
        if context is None:
            context = {}
        client = get_minio_client()
        if not client.bucket_exists(self.bucket):
            client.make_bucket(self.bucket)
        res = self.get_oids(cursor, obj, ids, name)
        for rid, oid in res.items():
            if oid:
                response = client.get_object(self.bucket, oid)
                try:
                    val = response.data
                    if context.get('bin_size', False) and val:
                        res[rid] = '%s' % human_size(val)
                    else:
                        res[rid] = base64.b64encode(val)
                finally:
                    response.close()
                    response.release_conn()
            else:
                res[rid] = False
        return res
