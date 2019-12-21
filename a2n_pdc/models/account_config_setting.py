
from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_pdc = fields.Many2one('account.account',string='Customer PDC Account')
    vendor_pdc = fields.Many2one('account.account',string='Vendor PDC Account')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            customer_pdc=int(self.env['ir.config_parameter'].sudo().get_param(
                'a2n_pdc.customer_pdc')),
            vendor_pdc=int(self.env['ir.config_parameter'].sudo().get_param(
                'a2n_pdc.vendor_pdc')),
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        cust = self.customer_pdc and self.customer_pdc.id or False
        vend = self.vendor_pdc and self.vendor_pdc.id or False

        param.set_param('a2n_pdc.customer_pdc', cust)
        param.set_param('a2n_pdc.vendor_pdc', vend)