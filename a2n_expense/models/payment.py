# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime

from itertools import groupby




class account_voucher_custom(models.Model):
    _inherit = "account.voucher"

    account_id = fields.Many2one('account.account', 'Account',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 domain="[('deprecated', '=', False),('user_type_id','=',3)]")





