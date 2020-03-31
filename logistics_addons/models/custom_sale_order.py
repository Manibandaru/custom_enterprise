
from odoo import fields, models,api,_
from odoo.fields import Date
from odoo.exceptions import UserError, ValidationError
import datetime



class SaleOrder(models.Model):
	_inherit = "sale.order"


	job_type = fields.Many2one('so.job.type', string='Job Type')
	client_order_ref = fields.Char(string='Cust Ref / Container Num', copy=False ,required=True )
	bl_no = fields.Char(string='B L Number', required=True)
	purchase_lines = fields.One2many('account.invoice.line','job_number')

	_sql_constraints = [
		('blno_unique', 'unique(bl_no)', 'This BL Number already Exists - it has to be unique!') ,
		('client_order_ref_unique', 'unique(client_order_ref)',
		 'This Container Number already Exists - it has to be unique!')
		]


	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			if 'company_id' in vals:
				vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
					'sale.order') or _('New')


			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')


		if vals['company_id']:

			current_year = int(datetime.datetime.now().year)
			print("Current Year",current_year)

			company = self.env['res.company'].search([('id','=',vals['company_id'])])
			if company.logistic_company :
				company_code = company.short_code
				if vals['job_type']:
					job_type = self.env['so.job.type'].search([('id', '=', vals['job_type'])])
					job_code =  job_type.code
					# vals['name'] = company_code + '/' + job_code + '/' + vals['name']

					vals['name'] =  vals['name'] +  '/' + job_code + '/' + str(current_year)

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

	@api.multi
	def action_view_purchase_invoice(self):
		#invoices = self.env['account.invoice']
		action = self.env.ref('account.action_vendor_bill_template').read()[0]

		action['domain'] = [('job_number', '=', self.id)]


		return action

	@api.multi
	def create_purchase_invoice(self):
		inv_vals = {
			'job_number': self.id,
			'name': self.client_order_ref or '',
			'date_invoice': fields.Date.today(),

			'type': 'in_invoice',
			'company_id': self.company_id.id,
			'user_id': self.user_id and self.user_id.id,
		}
		inv_obj = self.env['account.invoice']
		invoice = inv_obj.create(inv_vals)
		print(invoice.id)
		return self.action_view_purchase_invoice()
	# 	if self._context.get('open_invoices', False):
	# 		return sale_orders.action_view_invoice()
	# 	return {'type': 'ir.actions.act_window_close'}
	#

	@api.multi
	def _prepare_invoice(self):
		"""
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
		self.ensure_one()
		company_id = self.company_id.id
		journal_id = (self.env['account.invoice'].with_context(company_id=company_id or self.env.user.company_id.id)
			.default_get(['journal_id'])['journal_id'])
		if not journal_id:
			raise UserError(_('Please define an accounting sales journal for this company.'))
		invoice_vals = {
			'name': self.client_order_ref or '',
			'origin': self.name,
			'type': 'out_invoice',
			'account_id': self.partner_invoice_id.property_account_receivable_id.id,
			'partner_id': self.partner_invoice_id.id,
			'partner_shipping_id': self.partner_shipping_id.id,
			'journal_id': journal_id,
			'currency_id': self.pricelist_id.currency_id.id,
			'comment': self.note,
			'payment_term_id': self.payment_term_id.id,
			'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
			'company_id': company_id,
			'user_id': self.user_id and self.user_id.id,
			'team_id': self.team_id.id,
			'transaction_ids': [(6, 0, self.transaction_ids.ids)],
			'bl_number': self.client_order_ref,
			'container_no': self.container_no,
			'job_number':self.id,

		}
		return invoice_vals


class JobType_so(models.Model):
	_name = 'so.job.type'
	_rec_name = 'name'


	name = fields.Char('Name')
	code = fields.Char('Code')
