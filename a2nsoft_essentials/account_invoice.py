# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime

from itertools import groupby




class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_validate(self):
        for invoice in self.filtered(lambda invoice: invoice.partner_id not in invoice.message_partner_ids):
            invoice.message_subscribe([invoice.partner_id.id])

            # Auto-compute reference, if not already existing and if configured on company
            if not invoice.reference and invoice.type == 'out_invoice':
                invoice.reference = ''

            # DO NOT FORWARD-PORT.
            # The reference is copied after the move creation because we need the move to get the invoice number but
            # we need the invoice number to get the reference.
            invoice.move_id.ref = invoice.reference
        self._check_duplicate_supplier_reference()

        return self.write({'state': 'open'})