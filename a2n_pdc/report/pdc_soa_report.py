
import time
from odoo import api, fields, models


class ReportOverdue(models.AbstractModel):
    _inherit = 'report.soa_report.acc_statemnt_view'

    @api.multi
    def get_pdc_details(self,docids):
        print('Docids',docids)
        pdc_lines = {}
        for partner_id in docids:

            query = """  select id,cheque_no,cheque_date,payment_date,amount from account_payment where partner_id = """ + str(partner_id)+ """AND state ='pdc' """
            self.env.cr.execute(query)
            tmp = self.env.cr.dictfetchall()
            print("tmp",tmp)
            pdc_lines[partner_id] = tmp
        print("pdc_lines",pdc_lines)
        return pdc_lines

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
                currency = line['currency_id'] and self.env['res.currency'].browse(
                    line['currency_id']) or company_currency
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    totals[partner_id][currency] = dict((fn, 0.0) for fn in ['due', 'paid', 'mat', 'total', 'amount'])
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
            pdc_details = self.get_pdc_details(docids)
            print("pdc_details",pdc_details)
            print("lines_to_display",lines_to_display)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(docids),
            'time': time,
            'Lines': lines_to_display,
            'Totals': totals,
            'Date': fields.date.today(),
            "Pdc":pdc_details
        }