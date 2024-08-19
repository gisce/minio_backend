# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from destral import testing
from osv import osv, fields
from azure_backend.fields import AzureBlobFile
from azure_backend.azure_backend import get_azure_blob_client, get_object
from azure.core.exceptions import ResourceNotFoundError
import base64
from slugify import slugify


class AzureModel(osv.osv):
    _name = 'azure.model'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': AzureBlobFile('File', 'test')
    }


class AzureModelSubFolder(osv.osv):
    _name = 'azure.model.sub'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': AzureBlobFile('File', 'test', subfolder='foo')
    }


class AzureModelSlug(osv.osv):
    _name = 'azure.model.slug'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': AzureBlobFile('File', 'test_to_Slugià')
    }


class TestAzureBackend(testing.OOTestCaseWithCursor):

    def test_raises_exception_if_not_configured(self):
        from tools import config
        old_value = config.get('azure_connection_string')
        config['azure_connection_string'] = None
        with self.assertRaises(ValueError):
            get_azure_blob_client()
        config['azure_connection_string'] = old_value

    def test_store_on_azure(self):
        cursor = self.cursor
        uid = self.uid
        AzureModel()
        osv.class_pool['azure.model'].createInstance(
            self.openerp.pool, 'azure_backend', cursor
        )
        obj = self.openerp.pool.get('azure.model')
        obj._auto_init(cursor)

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'azure_model/{}_file'.format(obj_id)
        client = get_azure_blob_client()
        self.assertEqual(
            get_object(client, 'test', path),
            content
        )

    def test_store_on_azure_with_subfolder(self):
        cursor = self.cursor
        uid = self.uid
        AzureModelSubFolder()
        osv.class_pool['azure.model.sub'].createInstance(
            self.openerp.pool, 'azure_model_sub', cursor
        )
        obj = self.openerp.pool.get('azure.model.sub')
        obj._auto_init(cursor)

        content = b'TEST'
        subfolder = 'foo'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'azure_model_sub/{}/{}_file'.format(subfolder, obj_id)
        client = get_azure_blob_client()
        self.assertEqual(
            get_object(client, 'test', path),
            content
        )

    def test_remove_on_azure_with_subfolder(self):
        cursor = self.cursor
        uid = self.uid
        AzureModelSubFolder()
        osv.class_pool['azure.model.sub'].createInstance(
            self.openerp.pool, 'azure_backend_sub', cursor
        )
        obj = self.openerp.pool.get('azure.model.sub')
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
        client = get_azure_blob_client()
        path = 'azure_model_sub/{}/{}_file'.format(subfolder, obj_id)
        with self.assertRaises(ResourceNotFoundError):
            get_object(client, 'test', path)

    def test_remove_on_azure(self):
        cursor = self.cursor
        uid = self.uid
        AzureModel()
        osv.class_pool['azure.model'].createInstance(
            self.openerp.pool, 'azure_backend', cursor
        )
        obj = self.openerp.pool.get('azure.model')
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
        client = get_azure_blob_client()
        path = 'azure_model/{}_file'.format(obj_id)
        with self.assertRaises(ResourceNotFoundError):
            get_object(client, 'test', path)

    def test_saves_with_filename_if_is_in_context(self):

        cursor = self.cursor
        uid = self.uid
        AzureModel()
        osv.class_pool['azure.model'].createInstance(
            self.openerp.pool, 'azure_backend', cursor
        )
        obj = self.openerp.pool.get('azure.model')
        obj._auto_init(cursor)

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        }, context={'file_filename': 'test.txt'})

        client = get_azure_blob_client()
        path = 'azure_model/{}_test.txt'.format(obj_id)
        self.assertEqual(
            get_object(client, 'test', path),
            content
        )

        # Now rename the file
        new_content = b'TEST 2'
        obj.write(cursor, uid, [obj_id], {
            'file': base64.b64encode(new_content)
        }, context={'file_filename': 'test2.txt'})

        path = 'azure_model/{}_test2.txt'.format(obj_id)
        self.assertEqual(
            get_object(client, 'test', path),
            new_content
        )

        # Old object are remove
        path = 'azure_model/{}_test.txt'.format(obj_id)
        with self.assertRaises(ResourceNotFoundError):
            get_object(client, 'test', path)

    def test_saves_with_subfolder_if_is_in_context(self):

        cursor = self.cursor
        uid = self.uid
        AzureModel()
        osv.class_pool['azure.model'].createInstance(
            self.openerp.pool, 'azure_backend', cursor
        )
        obj = self.openerp.pool.get('azure.model')
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

        client = get_azure_blob_client()
        path = 'azure_model/{}/{}_test.txt'.format(subfolder, obj_id)
        self.assertEqual(
            get_object(client, 'test', path),
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

        path = 'azure_model/{}_test2.txt'.format(obj_id)
        self.assertEqual(
            get_object(client, 'test', path),
            new_content
        )

        # Old object are remove
        path = 'azure_model/{}/{}_test.txt'.format(subfolder, obj_id)
        with self.assertRaises(ResourceNotFoundError):
            get_object(client, 'test', path)

    def test_store_on_azure_slug(self):
        cursor = self.cursor
        uid = self.uid
        AzureModelSlug()
        osv.class_pool['azure.model.slug'].createInstance(
            self.openerp.pool, 'azure_backend', cursor
        )
        obj = self.openerp.pool.get('azure.model.slug')
        obj._auto_init(cursor)
        self.assertEqual(obj._columns['file'].container_name, slugify('test_to_Slugià'))

        content = b'TEST'

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode(content)
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode(content))

        path = 'azure_model_slug/{}_file'.format(obj_id)
        client = get_azure_blob_client()
        self.assertEqual(
            get_object(client, slugify('test_to_Slugià'), path),
            content
        )
