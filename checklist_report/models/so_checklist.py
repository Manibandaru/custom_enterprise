from odoo import models, fields, api, _

import datetime




class so_checklist(models.Model):
    _name = 'so.checklist'


    sale_order_id = fields.Many2one('sale.order',string='JOB Number')
    eta = fields.Date('ETA')
    free_time = fields.Integer('Free Time')
    bl_status=fields.Selection([('Original','Original'),('Surrender','Surrender')])
    do = fields.Float('DO Amount')
    demmurage = fields.Float('Demmurage Amount')

    so_date = fields.Datetime('SO Date')
    so_partner = fields.Many2one('res.partner')
    job_type = fields.Many2one('so.job.type','Job Type')
    bl_number = fields.Char('B/L Number')
    container_no = fields.Char('Container Number')
    state = fields.Selection([ ('draft','Draft'),('cancel','Canceled'),('validate','Validated')     ],default='draft')

    invoice_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')   ],string='Invoice')
    pack_list_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')    ],string='Packing List')
    certificate_origin_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')    ],string='Certificate of Origin')
    bl_awb_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')    ],string='BL/AWB')
    phyto_certificate_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')    ],string='Phyto Certificate')
    health_certificate_doc =fields.Selection([('Orginal','Original'),('Copy','Copy')    ],string='Health Certificate')


    @api.multi
    @api.onchange('sale_order_id')
    def onchage_sale_order(self):
        for record in self:
            record.so_date = []
            record.so_partner = []
            record.job_type = []

            if record.sale_order_id:
                record.so_date = record.sale_order_id.confirmation_date
                record.so_partner =record.sale_order_id.partner_id
                if record.sale_order_id.job_type:
                    record.job_type = record.sale_order_id.job_type.id

    @api.multi
    def cancel(self):
        for record in self:
            if record.state in ('draft','validate'):
                record.state='cancel'

    @api.multi
    def validate(self):
        for record in self:
            if record.state in ('draft','cancel'):
                record.state = 'validate'

    @api.multi
    def reset_to_draft(self):
        for record in self:
            if record.state == 'cancel':
                record.state = 'draft'


