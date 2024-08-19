from __future__ import absolute_import, unicode_literals
import base64
from destral import testing
from azure_backend.azure_backend import get_azure_blob_client


class TestIrAttachmentAzure(testing.OOTestCaseWithCursor):
    def test_create_attachment_stores_in_azure(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = b'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test.txt',
            'datas': base64.b64encode(content)
        })

        client = get_azure_blob_client()
        container_client = client.get_container_client('attachments')
        self.assertTrue(container_client.exists())
        object_path = 'ir_attachment/{}_test.txt'.format(attach_id)
        blob_client = container_client.get_blob_client(object_path)
        downloader = blob_client.download_blob()
        val = downloader.readall()
        self.assertEqual(val, content)

    def test_write_attachment_stores_in_azure(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = b'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test2.txt',
            'datas': base64.b64encode(content)
        })

        new_content = b'THIS IS A MODIFIED TEST FILE!'

        attach_obj.write(cursor, uid, [attach_id], {
            'datas': base64.b64encode(new_content)
        })

        client = get_azure_blob_client()
        container_client = client.get_container_client('attachments')
        self.assertTrue(container_client.exists())
        object_path = 'ir_attachment/{}_test2.txt'.format(attach_id)
        blob_client = container_client.get_blob_client(object_path)
        downloader = blob_client.download_blob()
        val = downloader.readall()
        self.assertEqual(val, new_content)

    def test_unlink_attachment_removes_file_in_azure(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = b'THIS IS A TEST FILE!'

        attach_id = attach_obj.create(cursor, uid, {
            'name': 'This is a description',
            'datas_fname': 'test.txt',
            'datas': base64.b64encode(content)
        })

        attach_obj.unlink(cursor, uid, [attach_id])

        client = get_azure_blob_client()
        container_client = client.get_container_client('attachments')

        object_path = 'ir_attachment/{}_test.txt'.format(attach_id)
        blob_client = container_client.get_blob_client(object_path)
        from azure.core.exceptions import ResourceNotFoundError
        with self.assertRaises(ResourceNotFoundError) as azure_exc:
            blob_client.download_blob()

    def test_read_attachment_from_azure(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        attach_obj = pool.get('ir.attachment')

        content = b'THIS IS A TEST FILE!'

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
