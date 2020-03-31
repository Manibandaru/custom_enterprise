
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
	vendor_id = fields.Many2one('res.partner',string='Vendor',default = lambda self: self.invoice_id.partner_id.id)

	@api.onchange('product_id')
	def onchange_product_id(self):
		for record in self:
			if record.invoice_id.job_number:
				record.job_number = record.invoice_id.job_number.id
				record.account_analytic_id = record.invoice_id.job_number.analytic_account_id.id



	@api.onchange('job_number')
	def job_onchange(self):
		for record in self:
			if record.job_number:
				record.account_analytic_id = record.job_number.analytic_account_id.id




