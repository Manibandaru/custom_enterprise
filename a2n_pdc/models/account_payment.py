# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime

from itertools import groupby




class account_payment(models.Model):
    _inherit = "account.payment"


    pay_mode = fields.Selection([('bank','Bank'),('cash','Cash'),('cheque','Cheque')],string='Payment Mode')

    cheque_type= fields.Selection([('cdc','Current Dated'),('pdc','Post Dated')])
    cheque_date = fields.Date('Cheque Date')
    cheque_no = fields.Char('Cheque Number')
    pdc_entry = fields.Many2one('account.move',string='PDC Entry')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
                              ('cancelled', 'Cancelled'),('pdc','PDC')], readonly=True, default='draft', copy=False, string="Status")

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)


            move = rec._create_payment_entry(amount)
            persist_move_name = move.name

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
                persist_move_name += self._get_move_name_transfer_separator() + transfer_debit_aml.move_id.name

            if self.pay_mode != 'cheque' and self.cheque_type != 'pdc':
                rec.write({'state': 'posted', 'move_name': persist_move_name})
            else:
                rec.write({'state': 'pdc', 'move_name': persist_move_name})
        return True



    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        if self.pay_mode == 'cheque' and self.cheque_type=='pdc':
            #print(error)
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.cheque_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        else:
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            #print("liquidity_aml_dict",liquidity_aml_dict)
            if self.pay_mode == 'cheque' and self.cheque_type=='pdc':

                param = self.env['ir.config_parameter']
                if self.partner_type=='customer':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.customer_pdc')])
                elif self.partner_type == 'supplier':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.vendor_pdc')])
                param_obj = self.env['ir.config_parameter'].browse(parameter_id.id)
                print("param_obj",param_obj.value)
                liquidity_aml_dict.update({'account_id':int(param_obj.value)})

            aml_obj.create(liquidity_aml_dict)

        #validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()
        #assigning pdc entry
        if self.pay_mode=='cheque' and self.cheque_type=='pdc':
            self.pdc_entry = move.id
        #reconcile the invoice receivable/payable line(s) with the payment
        if self.invoice_ids:
            self.invoice_ids.register_payment(counterpart_aml)

        return move



    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id

        move_vals = {
            'date': self.cheque_date if self.pay_mode=='cheque' else  self.payment_date ,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }

        name = False
        if self.move_name:
            names = self.move_name.split(self._get_move_name_transfer_separator())
            if self.payment_type == 'transfer':
                if journal == self.destination_journal_id and len(names) == 2:
                    name = names[1]
                elif journal == self.destination_journal_id and len(names) != 2:
                    # We are probably transforming a classical payment into a transfer
                    name = False
                else:
                    name = names[0]
            else:
                name = names[0]

        if name:
            move_vals['name'] = name
        return move_vals

    def _get_move_vals_pdc(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id

        move_vals = {
            'date': self.cheque_date if self.pay_mode=='cheque' else  self.payment_date ,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }

        name = False

        if name:
            move_vals['name'] = name
        return move_vals


    @api.multi
    def pdc_release(self):
        print('')
        for record in self:
            if record.state not in 'pdc':
                raise ValidationError(_('You cannot Release a Non PDC Cheque'))

            if self.payment_type=='inbound':
                aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.amount, self.currency_id, self.company_id.currency_id)

                move_vals=self._get_move_vals_pdc()
                move_vals.update({'date':datetime.today()})
                move = self.env['account.move'].create(move_vals)


                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id, 'account_id':self.journal_id.default_debit_account_id.id})
                print('counterpart_aml_dict',counterpart_aml_dict)
                counterpart_aml = aml_obj.create(counterpart_aml_dict)


                liquidity_aml_dict=[]
                amount=self.amount
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                param = self.env['ir.config_parameter']
                if self.partner_type == 'customer':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.customer_pdc')])
                elif self.partner_type == 'supplier':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.vendor_pdc')])
                param_obj = self.env['ir.config_parameter'].browse(parameter_id.id)
                liquidity_aml_dict.update({'account_id':int(param_obj.value)})
                print('liquidity_aml_dict',liquidity_aml_dict)
                aml_obj.create(liquidity_aml_dict)

                if not self.journal_id.post_at_bank_rec:
                    move.post()
                record.write({'state': 'posted'})
            else:
                aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                debit, credit, amount_currency, currency_id = aml_obj.with_context(
                    date=self.payment_date)._compute_amount_fields(self.amount, self.currency_id,
                                                                   self.company_id.currency_id)

                move_vals = self._get_move_vals_pdc()
                move_vals.update({'date': datetime.today()})
                move = self.env['account.move'].create(move_vals)

                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))

                param = self.env['ir.config_parameter']
                if self.partner_type == 'customer':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.customer_pdc')])
                elif self.partner_type == 'supplier':
                    parameter_id = param.search([('key', '=', 'a2n_pdc.vendor_pdc')])
                param_obj = self.env['ir.config_parameter'].browse(parameter_id.id)

                counterpart_aml_dict.update(
                    {'currency_id': currency_id, 'account_id': int(param_obj.value)})
                print('counterpart_aml_dict--payment', counterpart_aml_dict)
                counterpart_aml = aml_obj.create(counterpart_aml_dict)

                liquidity_aml_dict = []
                amount = self.amount
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))

                liquidity_aml_dict.update({'account_id': self.journal_id.default_credit_account_id.id})
                print('liquidity_aml_dict', liquidity_aml_dict)
                aml_obj.create(liquidity_aml_dict)

                if not self.journal_id.post_at_bank_rec:
                    move.post()
                record.write({'state': 'posted'})
        return move


    @api.multi
    def pdc_bounce(self):
        for record in self:
            if not record.state == 'pdc' and not record.pdc_entry:
                raise ValidationError(_("Only Payments which are in PDC state can be Bounced "))
            print('Bounce Call',record.pdc_entry)
            record.pdc_entry.button_cancel()
            record.write({'state':'cancelled'})
