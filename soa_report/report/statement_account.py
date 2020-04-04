
import time
from odoo import api, fields, models


class ReportOverdue(models.AbstractModel):
    _name = 'report.soa_report.acc_statemnt_view'

    def _get_account_move_lines(self, partner_ids):
        res = {x: [] for x in partner_ids}
        self.env.cr.execute("SELECT m.name AS move_id, l.date,ai.origin,ai.amount_total AS invoice , l.name, l.ref, l.date_maturity, l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
            "CASE WHEN at.type = 'receivable' "
                "THEN SUM(l.debit) "
                "ELSE SUM(l.credit * -1) "
            "END AS debit, "
            "CASE WHEN at.type = 'receivable' "
                "THEN SUM(l.credit) "
                "ELSE SUM(l.debit * -1) "
            "END AS credit, "
            "CASE WHEN l.date_maturity < %s "
                "THEN SUM(l.debit - l.credit) "
                "ELSE 0 "
            "END AS mat "
            "FROM account_move_line l "
            "JOIN account_account_type at ON (l.user_type_id = at.id) "
            "JOIN account_move m ON (l.move_id = m.id) "
            "LEFT JOIN account_invoice ai ON (l.invoice_id = ai.id)"
            "WHERE l.partner_id IN %s AND at.type IN ('receivable', 'payable') AND l.full_reconcile_id IS NULL GROUP BY l.date, l.name, l.ref, l.date_maturity, l.partner_id, at.type, l.blocked, l.amount_currency, l.currency_id, l.move_id, m.name,ai.origin,ai.amount_total", (((fields.date.today(), ) + (tuple(partner_ids),))))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        #print("partner_idspartner_ids",partner_ids)
        for partner in partner_ids:
            p =self.env['res.partner'].browse(partner)
            amls = p.unreconciled_aml_ids
            print(amls)
            vals =[]
            for l in amls:
                #print(l.amount_residual_currency if l.currency_id else l.amount_residual)
                dict={'move_id':l.move_id.name,'name':l.name, 'date':l.date ,'date_maturity':  l.date_maturity , 'origin':l.invoice_id.origin ,'bl_no':l.invoice_id.bl_number,'container_no':l.invoice_id.container_no, 'ref':l.ref , 'credit':l.credit, 'debit':l.debit,'invoice_amount': l.invoice_id.amount_total if l.invoice_id else 0.0 , 'amount':l.amount_residual_currency if l.currency_id else l.amount_residual ,
                     'payment_id':l.payment_id, 'currency_id':l.currency_id , 'amount_currency':l.amount_currency , 'mat':(l.amount_residual_currency if l.currency_id else l.amount_residual) if l.date_maturity < fields.date.today() else 0 , 'blocked':l.blocked }
                vals.append(dict)

            r = {partner:vals}
        # print("RRRRRRRRRR",r)
        # print("RESRES=",res)
        return r

    @api.model
    def _get_report_values(self, docids, data=None):
        totals = {}
        lines = self._get_account_move_lines(docids)
        lines_to_display = {}
        company_currency = self.env.user.company_id.currency_id

        for partner_id in docids:
            lines_to_display[partner_id] = {}
            totals[partner_id] = {}
            for line_tmp in lines[partner_id]:
                line = line_tmp.copy()
                currency = line['currency_id'] and self.env['res.currency'].browse(line['currency_id']) or company_currency
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    totals[partner_id][currency] = dict((fn, 0.0) for fn in ['due', 'paid', 'mat', 'total','amount'])
                if line['debit'] and line['currency_id']:
                    line['debit'] = line['amount_currency']
                if line['credit'] and line['currency_id']:
                    line['credit'] = line['amount_currency']
                if line['mat'] and line['currency_id']:
                    line['mat'] = line['amount_currency']
                if line['amount'] and line['currency_id']:
                    line['amount'] = line['amount_currency']
                lines_to_display[partner_id][currency].append(line)
                if not line['blocked']:
                    totals[partner_id][currency]['due'] += line['debit']
                    totals[partner_id][currency]['paid'] += line['credit']
                    totals[partner_id][currency]['mat'] += line['mat']
                    totals[partner_id][currency]['total'] += line['debit'] - line['credit']

                    totals[partner_id][currency]['amount'] += line['amount']

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(docids),
            'time': time,
            'Lines': lines_to_display,
            'Totals': totals,
            'Date': fields.date.today(),
        }


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.translate import _
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError



class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"
    #_description = "Follow-up Report"
    #_inherit = 'account.report'

    filter_partner_id = False

    def _get_options(self, previous_options=None):
        options = super()._get_options(previous_options)
        # It doesn't make sense to allow multicompany for these kind of reports
        # 1. Followup mails need to have the right headers from the right company
        # 2. Separation of business seems natural: a customer wouldn't know or care that the two companies are related
        if 'multi_company' in options:
            del options['multi_company']
        return options

    def _get_columns_name(self, options):
        """
        Override
        Return the name of the columns of the follow-ups report
        """
        headers = [{},
                   {'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Job Number'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Communication'), 'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _('Expected Date'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   {'name': _('Excluded'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   {'name': _('Total Due'), 'class': 'number o_price_total',
                    'style': 'text-align:right; white-space:nowrap;'}
                   ]
        if self.env.context.get('print_mode'):
            headers = headers[:5] + headers[7:]  # Remove the 'Expected Date' and 'Excluded' columns
        return headers

    def _get_lines(self, options, line_id=None):
        """
        Override
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []
        lang_code = partner.lang or self.env.user.lang or 'en_US'

        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.user.company_id):
            if l.company_id == self.env.user.company_id:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date',
                                'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = aml.invoice_id.name or aml.name
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date,
                                                lang_code=lang_code) if aml.expected_pay_date else ''
                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    date_due,
                    aml.invoice_id.origin,
                    move_line_name,
                    expected_pay_date + ' ' + (aml.internal_note or ''),
                    {'name': aml.blocked, 'blocked': aml.blocked},
                    amount,
                ]
                if self.env.context.get('print_mode'):
                    columns = columns[:4] + columns[6:]
                lines.append({
                    'id': aml.id,
                    'invoice_id': aml.invoice_id.id,
                    'view_invoice_id': self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1],
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'has_invoice': bool(aml.invoice_id),
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [
                    total >= 0 and _('Total Due') or '', total_due]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 0,
                    'columns': [{'name': v} for v in
                                [''] * (3 if self.env.context.get('print_mode') else 5) + [_('Total Overdue'),
                                                                                           total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()
        return lines

    def _get_default_summary(self, options):
        """
        Override
        Return the overdue message of the company as the summary of the report
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        lang = partner.lang or self.env.user.lang or 'en_US'
        return self.env.user.company_id.with_context(lang=lang).overdue_msg or \
               self.env['res.company'].with_context(lang=lang).default_get(['overdue_msg'])['overdue_msg']

    def _get_report_manager(self, options):
        """
        Override
        Compute and return the report manager for the partner_id in options
        """
        domain = [('report_name', '=', 'account.followup.report'), ('partner_id', '=', options.get('partner_id')),
                  ('company_id', '=', self.env.user.company_id.id)]
        existing_manager = self.env['account.report.manager'].search(domain, limit=1)
        if existing_manager and not options.get('keep_summary'):
            existing_manager.write({'summary': self._get_default_summary(options)})
        if not existing_manager:
            existing_manager = self.env['account.report.manager'].create({
                'report_name': 'account.followup.report',
                'company_id': self.env.user.company_id.id,
                'partner_id': options.get('partner_id'),
                'summary': self._get_default_summary(options)})
        return existing_manager

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        """
        Override
        Compute and return the content in HTML of the followup for the partner_id in options
        """
        if additional_context is None:
            additional_context = {}
        partner = self.env['res.partner'].browse(options['partner_id'])
        additional_context['partner'] = partner
        additional_context['lang'] = partner.lang or self.env.user.lang or 'en_US'
        additional_context['invoice_address_id'] = self.env['res.partner'].browse(
            partner.address_get(['invoice'])['invoice'])
        additional_context['today'] = fields.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return super(AccountFollowupReport, self).get_html(options, line_id=line_id,
                                                           additional_context=additional_context)

    def _get_report_name(self):
        """
        Override
        Return the name of the report
        """
        return _('Followup Report')

    def _get_reports_buttons(self):
        """
        Override
        Return an empty list because this report doesn't contain any buttons
        """
        return []

    def _get_templates(self):
        """
        Override
        Return the templates of the report
        """
        templates = super(AccountFollowupReport, self)._get_templates()
        templates['main_template'] = 'account_reports.template_followup_report'
        templates['line_template'] = 'account_reports.line_template_followup_report'
        return templates

    @api.model
    def get_followup_informations(self, partner_id, options):
        """
        Return all informations needed by the view:
        - the report manager id
        - the content in HTML of the report
        - the state of the next_action
        """
        options['partner_id'] = partner_id
        report_manager_id = self._get_report_manager(options).id
        html = self.get_html(options)
        next_action = False
        if not options.get('keep_summary'):
            next_action = self.env['res.partner'].browse(partner_id).get_next_action()
        return {
            'report_manager_id': report_manager_id,
            'html': html,
            'next_action': next_action,
        }

    @api.model
    def send_email(self, options):
        """
        Send by mail the followup to the customer
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        email = self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice']).email
        options['keep_summary'] = True
        if email and email.strip():
            # When printing we need te replace the \n of the summary by <br /> tags
            body_html = self.with_context(print_mode=True, mail=True, lang=partner.lang or self.env.user.lang).get_html(
                options)
            start_index = body_html.find(b'<span>', body_html.find(b'<div class="o_account_reports_summary">'))
            end_index = start_index > -1 and body_html.find(b'</span>', start_index) or -1
            if end_index > -1:
                replaced_msg = body_html[start_index:end_index].replace(b'\n', b'')
                body_html = body_html[:start_index] + replaced_msg + body_html[end_index:]
            msg = _('Follow-up email sent to %s') % email
            # Remove some classes to prevent interactions with messages
            msg += '<br>' + body_html.decode('utf-8') \
                .replace('o_account_reports_summary', '') \
                .replace('o_account_reports_edit_summary_pencil', '') \
                .replace('fa-pencil', '')
            msg_id = partner.message_post(body=msg, message_type='email')
            email = self.env['mail.mail'].create({
                'mail_message_id': msg_id.id,
                'subject': _('%s Payment Reminder') % (self.env.user.company_id.name) + ' - ' + partner.name,
                'body_html': append_content_to_html(body_html, self.env.user.signature or '', plaintext=False),
                'email_from': self.env.user.email or '',
                'email_to': email,
                'body': msg,
            })
            partner.message_subscribe([partner.id])
            return True
        raise UserError(_('Could not send mail to partner because it does not have any email address defined'))

    @api.model
    def print_followups(self, records):
        """
        Print one or more followups in one PDF
        records contains either a list of records (come from an server.action) or a field 'ids' which contains a list of one id (come from JS)
        """
        res_ids = records['ids'] if 'ids' in records else records.ids  # records come from either JS or server.action
        for partner in self.env['res.partner'].browse(res_ids):
            partner.message_post(body=_('Follow-up letter printed'))
        return self.env.ref('account_reports.action_report_followup').report_action(res_ids)

    def _execute_followup_partner(self, partner):
        """
        If the customer is in_need_of_action, we have to send email, print letter and mark as done
        Return partner if it's necessary to print
        """
        if partner.followup_status == 'in_need_of_action':
            partner.send_followup_email()
            next_date = fields.datetime.now() + timedelta(days=self.env.user.company_id.days_between_two_followups)
            partner.update_next_action(
                options={'next_action_date': datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT),
                         'next_action_type': 'auto'})
            return partner
        return None

    @api.model
    def execute_followup(self, records):
        """
        Execute the actions to do with followups.
        """
        to_print = []
        for partner in records:
            partner_tmp = self._execute_followup_partner(partner)
            if partner_tmp:
                to_print.append(partner_tmp.id)
        if not to_print:
            return
        return self.print_followups(self.env['res.partner'].browse(to_print))


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import datetime, timedelta


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.report"
    _name = "account.partner.ledger"
    _description = "Partner Ledger"

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
    filter_cash_basis = False
    filter_all_entries = False
    filter_unfold_all = False
    filter_account_type = [{'id': 'receivable', 'name': _('Receivable'), 'selected': False}, {'id': 'payable', 'name': _('Payable'), 'selected': False}]
    filter_unreconciled = False
    filter_partner = True

    # TODO: remove when https://github.com/odoo/odoo/pull/31211 is merged and _lt is used above
    def _build_options(self, previous_options=None):
        self.filter_account_type = [{'id': 'receivable', 'name': _('Receivable'), 'selected': False}, {'id': 'payable', 'name': _('Payable'), 'selected': False}]
        return super(ReportPartnerLedger, self)._build_options(previous_options=previous_options)

    def _get_templates(self):
        templates = super(ReportPartnerLedger, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_partner_ledger_report'
        return templates

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('JOB Number')},
            {'name': _('BL Number')},
            {'name': _('Description')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        print('columns',self.env.context)
        if self.env.context.get('print_mode'):
            columns = columns[:2] + columns[3:5] + columns[6:9] + columns[10:]
            columns.append({'name': _(''), 'class': 'number'})
            columns.append({'name': _(''), 'class': 'number'})
            columns.append({'name': _(''), 'class': 'number'})

        return columns

    def _set_context(self, options):
        ctx = super(ReportPartnerLedger, self)._set_context(options)
        ctx['strict_range'] = True
        return ctx

    def _do_query_group_by_account(self, options, line_id):
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        # Create the currency table.
        user_company = self.env.user.company_id
        companies = self.env['res.company'].search([])
        rates_table_entries = []
        for company in companies:
            if company.currency_id == user_company.currency_id:
                rate = 1.0
            else:
                rate = self.env['res.currency']._get_conversion_rate(
                    company.currency_id, user_company.currency_id, user_company, datetime.today())
            rates_table_entries.append((company.id, rate, user_company.currency_id.decimal_places))
        currency_table = ','.join('(%s, %s, %s)' % r for r in rates_table_entries)
        with_currency_table = 'WITH currency_table(company_id, rate, precision) AS (VALUES %s)' % currency_table

        # Sum query
        debit_field = 'debit_cash_basis' if options.get('cash_basis') else 'debit'
        credit_field = 'credit_cash_basis' if options.get('cash_basis') else 'credit'
        balance_field = 'balance_cash_basis' if options.get('cash_basis') else 'balance'
        tables, where_clause, params = self.env['account.move.line']._query_get(
            [('account_id.internal_type', 'in', account_types)])
        query = '''
            SELECT
                \"account_move_line\".partner_id,
                SUM(ROUND(\"account_move_line\".''' + debit_field + ''' * currency_table.rate, currency_table.precision))     AS debit,
                SUM(ROUND(\"account_move_line\".''' + credit_field + ''' * currency_table.rate, currency_table.precision))    AS credit,
                SUM(ROUND(\"account_move_line\".''' + balance_field + ''' * currency_table.rate, currency_table.precision))   AS balance
            FROM %s
            LEFT JOIN currency_table                    ON currency_table.company_id = \"account_move_line\".company_id
            WHERE %s
            AND \"account_move_line\".partner_id IS NOT NULL
            GROUP BY \"account_move_line\".partner_id
        ''' % (tables, where_clause)
        if line_id:
            query = query.replace('WHERE', 'WHERE \"account_move_line\".partner_id = %s AND ')
            params = [str(line_id)] + params
        if options.get("unreconciled"):
            query = query.replace("WHERE", 'WHERE \"account_move_line\".full_reconcile_id IS NULL AND ')
        self._cr.execute(with_currency_table + query, params)
        query_res = self._cr.dictfetchall()
        return dict((res['partner_id'], res) for res in query_res)

    def _group_by_partner_id(self, options, line_id):
        partners = {}
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        date_from = options['date']['date_from']
        results = self._do_query_group_by_account(options, line_id)
        initial_bal_results = self.with_context(
            date_from=False, date_to=fields.Date.from_string(date_from) + timedelta(days=-1)
        )._do_query_group_by_account(options, line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids']), ('account_id.internal_type', 'in', account_types)]
        base_domain.append(('date', '>=', date_from))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if options.get('unreconciled'):
            base_domain.append(('full_reconcile_id', '=', False))
        for partner_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('partner_id', '=', partner_id))
            #browse the partner name and trust field in sudo, as we may not have full access to the record (but we still have to see it in the report)
            partner = self.env['res.partner'].sudo().browse(partner_id)
            partners[partner] = result
            partners[partner]['initial_bal'] = initial_bal_results.get(partner.id, {'balance': 0, 'debit': 0, 'credit': 0})
            partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
            partners[partner]['total_lines'] = 0
            if not context.get('print_mode'):
                partners[partner]['total_lines'] = self.env['account.move.line'].search_count(domain)
                offset = int(options.get('lines_offset', 0))
                limit = self.MAX_LINES
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date,id', limit=limit, offset=offset)
            else:
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date,id')

        # Add partners with an initial balance != 0 but without any AML in the selected period.
        prec = self.env.user.company_id.currency_id.rounding
        missing_partner_ids = set(initial_bal_results.keys()) - set(results.keys())
        for partner_id in missing_partner_ids:
            if not float_is_zero(initial_bal_results[partner_id]['balance'], precision_rounding=prec):
                #browse the partner name and trust field in sudo, as we may not have full access to the record (but we still have to see it in the report)
                partner = self.env['res.partner'].sudo().browse(partner_id)
                partners[partner] = {'balance': 0, 'debit': 0, 'credit': 0}
                partners[partner]['initial_bal'] = initial_bal_results[partner_id]
                partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
                partners[partner]['lines'] = self.env['account.move.line']
                partners[partner]['total_lines'] = 0

        return partners

    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        if line_id:
            line_id = int(line_id.split('_')[1]) or None
        elif options.get('partner_ids') and len(options.get('partner_ids')) == 1:
            #If a default partner is set, we only want to load the line referring to it.
            partner_id = options['partner_ids'][0]
            line_id = partner_id
        if line_id:
            if 'partner_' + str(line_id) not in options.get('unfolded_lines', []):
                options.get('unfolded_lines', []).append('partner_' + str(line_id))

        grouped_partners = self._group_by_partner_id(options, line_id)
        sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines')
        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner in sorted_partners:
            debit = grouped_partners[partner]['debit']
            credit = grouped_partners[partner]['credit']
            balance = grouped_partners[partner]['balance']
            initial_balance = grouped_partners[partner]['initial_bal']['balance']
            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            columns = [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit)]
            if self.env.context.get('print_mode'):
                columns = [ self.format_value(debit), self.format_value(credit)]

            if self.user_has_groups('base.group_multi_currency'):
                columns.append('')
            columns.append(self.format_value(balance))
            # don't add header for `load more`
            if offset == 0:
                lines.append({
                    'id': 'partner_' + str(partner.id),
                    'name': partner.name,
                    'columns': [{'name': v} for v in columns],
                    'level': 2,
                    'trust': partner.trust,
                    'unfoldable': True,
                    'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 7 if self.env.context.get('print_mode') else 9,
                })
            user_company = self.env.user.company_id
            used_currency = user_company.currency_id
            if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
                if offset == 0:
                    progress = initial_balance
                else:
                    progress = float(options.get('lines_progress', initial_balance))
                domain_lines = []
                amls = grouped_partners[partner]['lines']

                remaining_lines = 0
                if not context.get('print_mode'):
                    remaining_lines = grouped_partners[partner]['total_lines'] - offset - len(amls)

                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    date = amls.env.context.get('date') or fields.Date.today()
                    line_currency = line.company_id.currency_id
                    line_debit = line_currency._convert(line_debit, used_currency, user_company, date)
                    line_credit = line_currency._convert(line_credit, used_currency, user_company, date)
                    line_bl_number = line.invoice_id.bl_number or None
                    line_job_number = line.invoice_id.job_number.name or None
                    line_container_no = line.invoice_id.container_no or None
                    progress_before = progress
                    progress = progress + line_debit - line_credit
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    domain_columns = [line.journal_id.code, line.account_id.code, self._format_aml_name(line),
                                      line.date_maturity and format_date(self.env, line.date_maturity) or '',
                                      line.full_reconcile_id.name or '', line_job_number,line_bl_number,line_container_no,self.format_value(progress_before),
                                      line_debit != 0 and self.format_value(line_debit) or '',
                                      line_credit != 0 and self.format_value(line_credit) or '']
                    if self.user_has_groups('base.group_multi_currency'):
                        domain_columns.append(self.with_context(no_format=False).format_value(line.amount_currency, currency=line.currency_id) if line.amount_currency != 0 else '')
                    domain_columns.append(self.format_value(progress))
                    columns = [{'name': v} for v in domain_columns]
                    columns[3].update({'class': 'date'})
                    if self.env.context.get('print_mode'):
                        columns = columns[:1] + columns[2:4] + columns[5:8] + columns[9:]
                    domain_lines.append({
                        'id': line.id,
                        'parent_id': 'partner_' + str(partner.id),
                        'name': format_date(self.env, line.date),
                        'class': 'date',
                        'columns': columns,
                        'caret_options': caret_type,
                        'level': 4,
                    })

                # load more
                if remaining_lines > 0:
                    domain_lines.append({
                        'id': 'loadmore_%s' % partner.id,
                        'offset': offset + self.MAX_LINES,
                        'progress': progress,
                        'class': 'o_account_reports_load_more text-center',
                        'parent_id': 'partner_%s' % partner.id,
                        'name': _('Load more... (%s remaining)') % remaining_lines,
                        'colspan': 13 if self.user_has_groups('base.group_multi_currency') else 11,
                        'columns': [{}],
                    })
                lines += domain_lines

        if not line_id:
            total_columns = ['', '', '', '', '','','','', self.format_value(total_initial_balance), self.format_value(total_debit), self.format_value(total_credit)]
            if self.env.context.get('print_mode'):
                total_columns = total_columns[2:8] + total_columns[9:]
            if self.user_has_groups('base.group_multi_currency'):
                total_columns.append('')
            total_columns.append(self.format_value(total_balance))
            lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in total_columns],
            })

        return lines

    @api.model
    def _get_report_name(self):
        return _('Partner Ledger')

