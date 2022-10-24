import base64
from destral import testing
from minio_backend.minio_backend import get_minio_client
from minio.error import NoSuchKey


class TestIrAttachmentMinio(testing.OOTestCaseWithCursor):
    def test_create_attachment_stores_in_minio(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = 'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test.txt',
            'datas': base64.b64encode(content)
        })

        client = get_minio_client()
        self.assertTrue(client.bucket_exists('attachments'))
        object_path = 'ir_attachment/{}_test.txt'.format(attach_id)
        self.assertEqual(
            client.get_object('attachments', object_path).data,
            content
        )

    def test_write_attachment_stores_in_minio(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = 'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test2.txt',
            'datas': base64.b64encode(content)
        })

        new_content = 'THIS IS A MODIFIED TEST FILE!'

        attach_obj.write(cursor, uid, [attach_id], {
            'datas': base64.b64encode(new_content)
        })

        client = get_minio_client()
        self.assertTrue(client.bucket_exists('attachments'))
        object_path = 'ir_attachment/{}_test2.txt'.format(attach_id)
        self.assertEqual(
            client.get_object('attachments', object_path).data,
            new_content
        )

    def test_unlink_attachment_removes_file_in_minio(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = 'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test.txt',
            'datas': base64.b64encode(content)
        })

        attach_obj.unlink(cursor, uid, [attach_id])

        client = get_minio_client()
        object_path = 'ir_attachment/{}_test.txt'.format(attach_id)
        with self.assertRaises(NoSuchKey):
            client.get_object('attachments', object_path)

    def test_read_attachment_from_minio(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = 'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test.txt',
            'datas': base64.b64encode(content)
        })

        attach = attach_obj.read(cursor, uid, attach_id, ['datas'])
        self.assertEqual(
            attach['datas'],
            base64.b64encode(content)
        )
