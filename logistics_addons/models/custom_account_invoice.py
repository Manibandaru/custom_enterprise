
from odoo import fields, models,api,_


class CustomAccountInvoice(models.Model):
	_inherit = "account.invoice"


	job_number = fields.Many2one('sale.order' , string='Job Number')