from odoo import fields, models,api,_

class CustomResCompany(models.Model):
	_inherit = 'res.company'

	short_code = fields.Char('Code')
	logistic_company = fields.Boolean('Logistic Company')
