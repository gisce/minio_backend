# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from destral import testing
from osv import osv, fields
from minio_backend.fields import S3File
from minio_backend.minio_backend import get_minio_client
from minio.error import NoSuchKey
import base64
from slugify import slugify


class MiniModel(osv.osv):
    _name = 'minio.model'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': S3File('File', 'test')
    }


class MiniModelSubFolder(osv.osv):
    _name = 'minio.model.sub'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': S3File('File', 'test', subfolder='foo')
    }


class MiniModelSlug(osv.osv):
    _name = 'minio.model.slug'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': S3File('File', 'test_to_Slugià')
    }


class TestMinioBackend(testing.OOTestCaseWithCursor):

    def test_raises_exception_if_not_configured(self):
        from minio_backend.minio_backend import get_minio_client
        from tools import config
        old_value = config.get('minio_endpoin')
        config['minio_endpoint'] = None
        with self.assertRaises(ValueError):
            get_minio_client()
        config['minio_endpoint'] = old_value

    def test_store_on_minio(self):
        cursor = self.cursor
        uid = self.uid
        MiniModel()
        osv.class_pool['minio.model'].createInstance(
            self.openerp.pool, 'minio_backend', cursor
        )
        obj = self.openerp.pool.get('minio.model')
        obj._auto_init(cursor)

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'minio_model/{}_file'.format(obj_id)
        client = get_minio_client()
        self.assertEqual(
            client.get_object('test', path).data,
            content
        )

    def test_store_on_minio_with_subfolder(self):
        cursor = self.cursor
        uid = self.uid
        MiniModelSubFolder()
        osv.class_pool['minio.model.sub'].createInstance(
            self.openerp.pool, 'minio_model_sub', cursor
        )
        obj = self.openerp.pool.get('minio.model.sub')
        obj._auto_init(cursor)

        content = b'TEST'
        subfolder = 'foo'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'minio_model_sub/{}/{}_file'.format(subfolder, obj_id)
        client = get_minio_client()
        self.assertEqual(
            client.get_object('test', path).data,
            content
        )

    def test_remove_on_minio_with_subfolder(self):
        cursor = self.cursor
        uid = self.uid
        MiniModelSubFolder()
        osv.class_pool['minio.model.sub'].createInstance(
            self.openerp.pool, 'minio_backend_sub', cursor
        )
        obj = self.openerp.pool.get('minio.model.sub')
        obj._auto_init(cursor)
        subfolder = 'foo'
        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(b"TEST")
        })

        obj.write(cursor, uid, [obj_id], {'file': False})
        self.assertEqual(
            obj.read(cursor, uid, obj_id)['file'],
            False
        )
        client = get_minio_client()
        path = 'minio_model_sub/{}/{}_file'.format(subfolder, obj_id)
        with self.assertRaises(NoSuchKey):
            client.get_object('test', path)

    def test_remove_on_minio(self):
        cursor = self.cursor
        uid = self.uid
        MiniModel()
        osv.class_pool['minio.model'].createInstance(
            self.openerp.pool, 'minio_backend', cursor
        )
        obj = self.openerp.pool.get('minio.model')
        obj._auto_init(cursor)

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(b"TEST")
        })

        obj.write(cursor, uid, [obj_id], {'file': False})
        self.assertEqual(
            obj.read(cursor, uid, obj_id)['file'],
            False
        )
        client = get_minio_client()
        path = 'minio_model/{}_file'.format(obj_id)
        with self.assertRaises(NoSuchKey):
            client.get_object('test', path)

    def test_saves_with_filename_if_is_in_context(self):

        cursor = self.cursor
        uid = self.uid
        MiniModel()
        osv.class_pool['minio.model'].createInstance(
            self.openerp.pool, 'minio_backend', cursor
        )
        obj = self.openerp.pool.get('minio.model')
        obj._auto_init(cursor)

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        }, context={'file_filename': 'test.txt'})

        client = get_minio_client()
        path = 'minio_model/{}_test.txt'.format(obj_id)
        self.assertEqual(
            client.get_object('test', path).data,
            content
        )

        # Now rename the file
        new_content = b'TEST 2'
        obj.write(cursor, uid, [obj_id], {
            'file': base64.b64encode(new_content)
        }, context={'file_filename': 'test2.txt'})

        path = 'minio_model/{}_test2.txt'.format(obj_id)
        self.assertEqual(
            client.get_object('test', path).data,
            new_content
        )

        # Old object are remove
        path = 'minio_model/{}_test.txt'.format(obj_id)
        with self.assertRaises(NoSuchKey):
            client.get_object('test', path)

    def test_saves_with_subfolder_if_is_in_context(self):

        cursor = self.cursor
        uid = self.uid
        MiniModel()
        osv.class_pool['minio.model'].createInstance(
            self.openerp.pool, 'minio_backend', cursor
        )
        obj = self.openerp.pool.get('minio.model')
        obj._auto_init(cursor)

        content = b'TEST'
        subfolder = 'bar'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        }, context={
            'file_filename': 'test.txt',
            'subfolder': subfolder
            }
        )

        client = get_minio_client()
        path = 'minio_model/{}/{}_test.txt'.format(subfolder, obj_id)
        self.assertEqual(
            client.get_object('test', path).data,
            content
        )

        # Now rename the file
        new_content = b'TEST 2'
        obj.write(cursor, uid, [obj_id], {
            'file': base64.b64encode(new_content)
        }, context={
            'file_filename': 'test2.txt',
            'subfolder': subfolder
            }
        )

        path = 'minio_model/{}_test2.txt'.format(obj_id)
        self.assertEqual(
            client.get_object('test', path).data,
            new_content
        )

        # Old object are remove
        path = 'minio_model/{}/{}_test.txt'.format(subfolder, obj_id)
        with self.assertRaises(NoSuchKey):
            client.get_object('test', path)

    def test_store_on_minio_slug(self):
        cursor = self.cursor
        uid = self.uid
        MiniModelSlug()
        osv.class_pool['minio.model.slug'].createInstance(
            self.openerp.pool, 'minio_backend', cursor
        )
        obj = self.openerp.pool.get('minio.model.slug')
        obj._auto_init(cursor)
        self.assertEqual(obj._columns['file'].bucket, slugify('test_to_Slugià'))

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'minio_model_slug/{}_file'.format(obj_id)
        client = get_minio_client()
        self.assertEqual(
            client.get_object(slugify('test_to_Slugià'), path).data,
            content
        )