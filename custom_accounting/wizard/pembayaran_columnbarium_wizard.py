# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime

class AccountPaymentColWizard(models.TransientModel):
    _name = 'account.payment.columnbarium.wizard'

    # about header
    sale_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True, readonly=True)
    payment_mode = fields.Selection([
        ("on_payment", "On Payment"),
        ("others", "Others"),
    ], default='others', string="Payment Mode", readonly=True)
    criteria_type = fields.Selection([
        ("biaya", "Biaya"),
        ("lain-lain", "Lain-lain"),
        ('columnbarium','Columbarium')], default='columnbarium', readonly=True)
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today
    )

    # about amount
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=True,
        compute='_compute_currency_id',
        help="The payment's currency.")
    amount = fields.Monetary(currency_field='currency_id')
    discount = fields.Monetary(string="Discount", currency_field='currency_id')
    grand_amount = fields.Monetary(string="Grand Amount", currency_field='currency_id', compute="_compute_grand_amount")
    @api.depends('discount','amount')
    def _compute_grand_amount(self):
        self.grand_amount = self.amount - self.discount

    # about payment
    method_id = fields.Many2one('payment.method', string="Payment Method", required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, 
        check_company=True, domain="[('type', 'in', ('bank','cash')), ('company_id', '=', company_id)]",)
    account_titipan_id = fields.Many2one('account.account', string='Account Titipan', index=True, ondelete="restrict", required=True)
    account_discount_id = fields.Many2one('account.account', string='Account Discount', index=True, ondelete="restrict")

    # about company
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 store=True, readonly=True,
                                 compute='_compute_company_id')
    @api.depends('journal_id')
    def _compute_company_id(self):
        for move in self:
            move.company_id = move.journal_id.company_id or move.company_id or self.env.company

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.journal_id.currency_id or pay.journal_id.company_id.currency_id

    @api.onchange('method_id')
    def _onchange_method_id(self):
        if self.method_id:
            self.journal_id = self.method_id.journal_id
    
    def action_confirm(self):
        # line_vals_list = [
        #     # Liquidity line.
        #     {
        #         'name': 'Columnbarium',
        #         'date_maturity': self.date,
        #         'amount_currency': self.grand_amount,
        #         'currency_id': self.currency_id.id,
        #         'debit': self.grand_amount if self.grand_amount > 0.0 else 0.0,
        #         'credit': -self.grand_amount if self.grand_amount < 0.0 else 0.0,
        #         'partner_id': self.sale_id.partner_id.id,
        #         'account_id': self.journal_id.default_account_id.id,
        #     },
        #     # Receivable / Payable.
        #     {
        #         'name': 'Columnbarium',
        #         'date_maturity': self.date,
        #         'amount_currency': self.amount,
        #         'currency_id': self.currency_id.id,
        #         'debit': -self.amount if self.amount > 0.0 else 0.0,
        #         'credit': self.amount if self.amount < 0.0 else 0.0,
        #         'partner_id': self.sale_id.partner_id.id,
        #         'account_id': self.account_titipan_id.id,
        #         # 'no_voucher': self.no_voucher,
        #     },
        # ]

        detail = []
        detail.append([0,False,{
            'description': 'Hutang Titipan Columbarium',
            'account_id': self.account_titipan_id.id,
            'amount': self.amount,
        }])

        if self.discount > 0:
            detail.append([0,False,{
                'description': 'Discount Columbarium',
                'account_id': self.account_discount_id.id,
                'amount': self.discount * -1,
            }])

        pay = self.env['account.payment'].create({
                'partner_id': self.sale_id.partner_id.id,
                'currency_id': self.currency_id.id,
                'payment_type': self.payment_type,
                'payment_mode': self.payment_mode,
                'method_id': self.method_id.id,
                'partner_id': self.sale_id.partner_id.id,
                'amount': self.grand_amount,
                'date': self.date,
                'journal_id': self.journal_id.id,
                'payment_line_ids': detail
                # 'line_ids': line_vals_list,
            })
        if pay:
            pay.action_post()
            self.sale_id.write({'payment_id':pay.id})