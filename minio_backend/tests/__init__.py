from destral import testing
from osv import osv, fields
from minio_backend.fields import S3File
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

        obj_id = obj.create(cursor, uid, {
            'name': 'Foo',
            'file': base64.b64encode("TEST")
        })

        result = obj.read(cursor, uid, obj_id, ['file'])
        self.assertEqual(result['file'], base64.b64encode("TEST"))
