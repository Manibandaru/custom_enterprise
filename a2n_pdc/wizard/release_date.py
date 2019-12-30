# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime

from itertools import groupby




class account_pdc_release(models.TransientModel):
    _name = "pdc_release_date"

    release_date = fields.Date(string='Release Date')


    @api.multi
    def release_pdc(self):

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        docs.write({'bank_date':self.release_date})
        docs.pdc_release()
        return True