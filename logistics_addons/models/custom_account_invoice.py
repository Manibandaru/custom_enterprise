
from odoo import fields, models,api,_


class CustomAccountInvoice(models.Model):
	_inherit = "account.invoice"


	job_number = fields.Many2one('sale.order' , string='Job Number')
	bl_number = fields.Char(string='BL Number')
	container_no = fields.Char(string='Conatiner No')



class CustomAccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"

	@api.model
	def default_job(self):
		for record in self:
			if record.invoice_id.job_number:
				job_number = record.invoice_id.job_number.id
				return job_number


	job_number = fields.Many2one('sale.order' , string='Job Number',default=default_job )

	@api.onchange('product_id')
	def onchange_product_id(self):
		for record in self:
			if record.invoice_id.job_number:
				record.job_number = record.invoice_id.job_number.id






