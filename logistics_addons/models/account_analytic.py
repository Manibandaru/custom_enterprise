from odoo import fields, models,api,_
from odoo.fields import Date
from odoo.exceptions import UserError, ValidationError
import datetime


class account_analytic_group(models.Model):
    _inherit = 'account.analytic.group'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')