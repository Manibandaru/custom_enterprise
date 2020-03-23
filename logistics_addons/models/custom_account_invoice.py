
from odoo import fields, models,api,_


class CustomAccountInvoice(models.Model):
	_inherit = "account.invoice"


	job_number = fields.Many2one('sale.order' , string='Job Number')
	bl_number = fields.Char(string='BL Number')
	container_no = fields.Char(string='Conatiner No')