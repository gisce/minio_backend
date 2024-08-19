# encoding=utf-8
from __future__ import absolute_import, unicode_literals
from osv import osv
from azure_backend.fields import AzureBlobFile
from slugify import slugify
from tools import config


def azureize(vals):
    vals['datas_azure'] = vals['datas']
    vals['datas'] = False


def unazureize(vals):
    vals['datas'] = vals['datas_azure']
    del vals['datas_azure']


class IrAttachment(osv.osv):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def get_subfolder(self, vals, context):
        subfolder = context.get(
            'default_res_model',
            vals.get('res_model', None)
        )
        return subfolder

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if 'datas_fname' in vals:
            ctx['datas_azure_filename'] = slugify(
                vals['datas_fname'], separator='.'
            )
        if 'datas' in vals and vals['datas']:
            azureize(vals)
        ctx['subfolder'] = self.get_subfolder(vals, context)
        return super(IrAttachment, self).create(cursor, uid, vals, context=ctx)

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if 'datas' in vals:
            azureize(vals)
        if 'datas_fname' in vals:
            ctx['datas_azure_filename'] = slugify(
                vals['datas_fname'], separator='.'
            )
        ctx['subfolder'] = self.get_subfolder(vals, context)
        return super(IrAttachment, self).write(cursor, uid, ids, vals, context=ctx)

    def read(self, cursor, uid, ids, fields=None, context=None,
             load='_classic_read'):
        if fields and 'datas' in fields and 'datas_azure' not in fields:
            fields.append('datas_azure')
        res = super(IrAttachment, self).read(cursor, uid, ids, fields, context,
                                             load)
        if isinstance(ids, (list, tuple)):
            if res and 'datas' in res[0]:
                for attach in res:
                    if attach['datas_azure']:
                        unazureize(attach)
        else:
            if 'datas' in res and res['datas_azure']:
                unazureize(res)
        return res

    def unlink(self, cursor, uid, ids, context=None):
        self.write(cursor, uid, ids, {'datas': False})
        return super(IrAttachment, self).unlink(cursor, uid, ids, context)

    _columns = {
        'datas_azure': AzureBlobFile('Azure object', config.get('azure_bucket_attachment', 'attachments'))
    }


IrAttachment()
