# encoding=utf-8
from __future__ import absolute_import
from osv import osv
from minio_backend.fields import S3File
from slugify import slugify


def minioize(vals):
    vals['datas_minio'] = vals['datas']
    vals['datas'] = False


def unminioize(vals):
    vals['datas'] = vals['datas_minio']
    del vals['datas_minio']


class IrAttachment(osv.osv):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if 'datas_fname' in vals:
            ctx['datas_minio_filename'] = slugify(
                vals['datas_fname'], separator='.'
            )
        elif 'filename' in vals:
            ctx['datas_minio_filename'] = slugify(
                vals['filename'], separator='.'
            )
        if 'datas' in vals and vals['datas']:
            minioize(vals)

        ctx['subfolder'] = ctx.get('default_res_model')
        return super(IrAttachment, self).create(cursor, uid, vals, context=ctx)

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if 'datas' in vals:
            minioize(vals)
        if 'datas_fname' in vals:
            ctx['datas_minio_filename'] = slugify(
                vals['datas_fname'], separator='.'
            )
        elif 'filename' in vals:
            ctx['datas_minio_filename'] = slugify(
                vals['filename'], separator='.'
            )
        ctx['subfolder'] = ctx.get('default_res_model')
        return super(
            IrAttachment, self).write(cursor, uid, ids, vals, context=ctx
        )

    def read(self, cursor, uid, ids, fields=None, context=None,
             load='_classic_read'):
        if fields and 'datas' in fields and 'datas_minio' not in fields:
            fields.append('datas_minio')
        res = super(IrAttachment, self).read(cursor, uid, ids, fields, context,
                                             load)
        if isinstance(ids, (list, tuple)):
            if res and 'datas' in res[0]:
                for attach in res:
                    if attach['datas_minio']:
                        unminioize(attach)
        else:
            if 'datas' in res and res['datas_minio']:
                unminioize(res)
        return res

    def unlink(self, cursor, uid, ids, context=None):
        self.write(cursor, uid, ids, {'datas': False})
        return super(IrAttachment, self).unlink(cursor, uid, ids, context)

    _columns = {
        'datas_minio': S3File('Minio object', 'attachments')
    }


IrAttachment()
