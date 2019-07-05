
from odoo import fields, models,api,_


class SaleOrder(models.Model):
	_inherit = "sale.order"


	job_type = fields.Many2one('so.job.type', string='Job Type')

	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			if 'company_id' in vals:
				vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
					'sale.order') or _('New')


			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')


		if vals['company_id']:
			company = self.env['res.company'].search([('id','=',vals['company_id'])])
			if company.logistic_company :
				company_code = company.short_code
				if vals['job_type']:
					job_type = self.env['so.job.type'].search([('id', '=', vals['job_type'])])
					job_code =  job_type.code
					vals['name'] = company_code + '/' + job_code + '/' + vals['name']
				else:
					vals['name'] = company_code + '/' + vals['name']

				print("vals(name,partner id)=====",vals['name'],vals['partner_id'])
				#CREATE JOB
				job_vals= {'name':vals['name'] , 'partner_id' : vals['partner_id'] , 'company_id':vals['company_id'] }

				analytic = self.env['account.analytic.account'].create(job_vals)
				print('ANALYTIC============',analytic)
				vals['analytic_account_id'] = analytic.id

		# Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
		if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
			partner = self.env['res.partner'].browse(vals.get('partner_id'))
			addr = partner.address_get(['delivery', 'invoice'])
			vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
			vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
			vals['pricelist_id'] = vals.setdefault('pricelist_id',
												   partner.property_product_pricelist and partner.property_product_pricelist.id)
		result = super(SaleOrder, self).create(vals)



		return result


class JobType_so(models.Model):
	_name = 'so.job.type'
	_rec_name = 'name'


	name = fields.Char('Name')
	code = fields.Char('Code')
