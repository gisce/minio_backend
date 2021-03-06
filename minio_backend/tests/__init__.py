from destral import testing
from osv import osv, fields
from minio_backend.fields import S3File
from minio_backend.minio_backend import get_minio_client
from minio.error import NoSuchKey
import base64


class MiniModel(osv.osv):
    _name = 'minio.model'

    def _field_create(self, cr, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'file': S3File('File', 'test')
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

        content = 'TEST'

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
            'file': base64.b64encode("TEST")
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

        content = 'TEST'

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
        new_content = 'TEST 2'
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
