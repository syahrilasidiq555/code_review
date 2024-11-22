from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

import datetime
import calendar

MAP_CASH_BANK = [
                'asset_cash'
                ]

MAP_ACCOUNT_REVAL = [
                'asset_cash',
                'asset_receivable',
                'liability_payable',
                ]



class RevaluasiKurs(models.TransientModel):
    _name = 'revaluasi.kurs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Revaluasi Kurs'

    ref = fields.Char(string="Reference")  
    label = fields.Char(string="Label")

    # date = fields.Date('Date', default=fields.Date.context_today, required=True)
    year = fields.Integer(string='Year', required=True, default=lambda self: datetime.date.today().year)
    month = fields.Selection(
        selection=[
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "Afril"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month", tracking=True, required=True, default=lambda self: str(datetime.date.today().month)
    )

    journal_id = fields.Many2one('account.journal', string='Journal', required=True)

    def _defaultAccount(self):
        dtAcc = self.env['account.account'].search([('account_type','in',MAP_ACCOUNT_REVAL)])
        return dtAcc.ids
    account_ids = fields.Many2many('account.account', string='Account', domain=[('account_type', 'in', MAP_ACCOUNT_REVAL)], default=_defaultAccount)
    
    def _defaultCurrency(self):
        line_curr = []
        dt = self.env['res.currency'].search([('active','=',True),('id','!=',self.env.company.currency_id.id)])
        dtAcc = self.env['account.account'].search([('account_type','in',MAP_ACCOUNT_REVAL)])
        if dt:
            for i in dt:
                tmp = [0,0,{
                    'currency_id': i.id,
                    'rate_kurs': self.env['res.currency.rate'].search([('currency_id','=',i.id),('name','=',datetime.date.today())]).inverse_company_rate or 0
                }]
                line_curr.append(tmp)
        return line_curr
    revaluasi_line = fields.One2many('revaluasi.kurs.line','revaluasi_id', string="Lines", ondelete='cascade', copy=True, tracking=True, default=_defaultCurrency)
    
    @api.onchange('month','year')
    def _onchange_date(self):
        for i in self.revaluasi_line:
            i._onchange_kurs()
    
    def action_confirm(self):
        result = []
        # SET TGL AWAL DAN TGL AKHIR
        tgl_awal_bln = datetime.datetime(self.year, int(self.month), 1)
        day_of_month = calendar.monthrange(self.year, int(self.month))[1]
        tgl_akhir_bln = datetime.datetime(self.year, int(self.month), day_of_month)

        for i in self.revaluasi_line:
            self.env['res.currency.rate'].search([('name','=',tgl_akhir_bln),('currency_id','=',i.currency_id.id)]).write({'inverse_company_rate': i.rate_kurs})
            move_line = self.env['account.move.line'].search([
                '&', 
                ('date', '<=', tgl_akhir_bln), 
                ('account_id', 'not in', [i.realized_account_id.id, i.unrealized_account_id.id]),
                ('account_id.account_type','in',MAP_ACCOUNT_REVAL),
                ('account_id','in',self.account_ids.ids),
                ('amount_currency', '!=', False),('amount_currency', '!=', 0),
                ('currency_id','=', i.currency_id.id), 
                ('parent_state','=','posted'),
            ])
            map_coa = move_line.mapped('account_id')
            line_ids_det = []
            for i2 in map_coa:
                # SALDO
                line_saldo = self.env['account.move.line'].search([
                    '&',
                    ('date', '<=', tgl_akhir_bln), 
                    ('account_id', '=', i2.id),
                    ('currency_id', '=', i.currency_id.id),
                    ('amount_currency', '!=', False), ('amount_currency', '!=', 0),
                    ('parent_state', '=', 'posted'),
                ])

                # parsing SALDO
                debit_saldo = sum(line_saldo.mapped('debit'))
                credit_saldo = sum(line_saldo.mapped('credit'))
                amount_curr_saldo = sum(line_saldo.mapped('amount_currency'))

                balance = debit_saldo - credit_saldo
                balance_rate = i.currency_id._convert(amount_curr_saldo, self.env.company.currency_id, self.env.company, tgl_akhir_bln)
                balance_value = balance - balance_rate

                if balance_value != 0 and balance != 0:
                    acc_res = 0
                    if i2.account_type in MAP_CASH_BANK:
                        acc_res = i.realized_account_id.id
                    else:
                        acc_res = i.unrealized_account_id.id

                    # VALUE AFTER SELISIH RATE
                    det = {
                        'name': str(self.label) + ' ' + str(i.currency_id.name) + ' ' + tgl_akhir_bln.strftime('%B'),
                        'debit': balance_value < 0.0 and -balance_value or 0.0,
                        'credit': balance_value > 0.0 and balance_value or 0.0,
                        'date_maturity': tgl_akhir_bln.strftime('%Y-%m-%d'),
                        'account_id': i2.id,
                        'currency_id': i.currency_id.id,
                        'amount_currency': 0,
                    }
                    line_ids_det.append((0,0,det))

                    det = {
                        'name': str(self.label) + ' ' + str(i.currency_id.name) + ' ' + tgl_akhir_bln.strftime('%B'),
                        'debit': balance_value > 0.0 and balance_value or 0.0,
                        'credit': balance_value < 0.0 and -balance_value or 0.0,
                        'date_maturity': tgl_akhir_bln.strftime('%Y-%m-%d'),
                        'account_id': acc_res,
                        'currency_id': i.currency_id.id, #self.env.company.currency_id.id,
                        'amount_currency': 0,
                    }
                    line_ids_det.append((0,0,det))

            all_move_vals = {
                'date': tgl_akhir_bln.strftime('%Y-%m-%d'),
                'ref': str(self.ref) + ' ' + str(i.currency_id.name),
                'journal_id': self.journal_id.id,
                'line_ids': line_ids_det
            }

            # create account move
            if line_ids_det != []:
                am = self.env['account.move'].with_context(default_type='entry')
                moves = am.create(all_move_vals)
                result.append(moves.id)

        # =============================================
        if result:
            open_form = {
                'name': _("Journal Revaluasi Kurs"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', result)],
                'context': {'create': False},
            }
            return open_form
        else:
            ValidationError("Currency Exchange Rate input failed. Please check again and make sure data is correct.")
    

class RevaluasiKursLine(models.TransientModel):
    _name = 'revaluasi.kurs.line'

    revaluasi_id = fields.Many2one('revaluasi.kurs',  string='Lines', readonly=True, copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency')
    realized_account_id = fields.Many2one('account.account', string='Realized Account', index=True, ondelete="restrict", required=True)
    unrealized_account_id = fields.Many2one('account.account', string='Unrealized Account', index=True, ondelete="restrict", required=True)
    rate_kurs = fields.Float(string="Kurs")
    
    @api.onchange('currency_id')
    @api.depends('currency_id')
    def _onchange_kurs(self):
        for rec in self:
            tgl_awal_bln = datetime.datetime(rec.revaluasi_id.year, int(rec.revaluasi_id.month), 1)
            day_of_month = calendar.monthrange(rec.revaluasi_id.year, int(rec.revaluasi_id.month))[1]
            tgl_akhir_bln = datetime.datetime(rec.revaluasi_id.year, int(rec.revaluasi_id.month), day_of_month)
            dtKurs = self.env['res.currency.rate'].search([('currency_id','=',rec.currency_id.id),('name','=',tgl_akhir_bln)])
            if dtKurs:
                rec.rate_kurs = dtKurs.inverse_company_rate
            else:
                rec.rate_kurs = 0
