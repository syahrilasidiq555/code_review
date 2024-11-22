# -*- coding: utf-8 -*-
from collections import defaultdict
from xml.dom import ValidationErr
from lxml import etree
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict
from datetime import datetime

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    no_voucher = fields.Char(string="Voucher", tracking=True)
    pr_id = fields.Many2one('account.payment.requisition')
    method_id = fields.Many2one('payment.method', string="Payment Method", required=True)
    grand_amount = fields.Monetary(currency_field='currency_id', compute="_compute_grand_amount", store=True)
    payment_line_disc_ids = fields.One2many('account.payment.register.line.disc', 'line_id', string='Potongan')

    def _default_group_payment(self):
        active_ids = self._context.get("active_ids")
        return len(active_ids) > 1
    group_payment = fields.Boolean(default=_default_group_payment)

    @api.depends('amount', 'payment_line_disc_ids')
    def _compute_grand_amount(self):
        for rec in self:
            rec.grand_amount = rec.amount - sum(rec.payment_line_disc_ids.mapped('amount'))

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
    def _compute_amount(self):
        for wizard in self:
            if not wizard.pr_id:
                if wizard.source_currency_id == wizard.currency_id:
                    # Same currency.
                    wizard.amount = wizard.source_amount_currency
                elif wizard.currency_id == wizard.company_id.currency_id:
                    # Payment expressed on the company's currency.
                    wizard.amount = wizard.source_amount
                else:
                    # Foreign currency on payment different than the one set on the journal entries.
                    amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                    wizard.amount = amount_payment_currency

    @api.onchange('method_id')
    def _onchange_method_id(self):
        if self.method_id:
            self.journal_id = self.method_id.journal_id
    
    def _create_payment_vals_from_wizard(self):
        values = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()

        line_disc = []
        for i in self.payment_line_disc_ids:
            det = [0, False, {
                u'account_id': i.account_id.id,
                u'currency_id': i.currency_id.id,
                u'amount': i.amount,
                u'description': i.description,
            }]
            line_disc.append(det)

        values.update({
            'method_id': self.method_id.id,
            'loa_type': False,
            'no_voucher': self.no_voucher,
            'payment_line_disc_ids': line_disc,
            'amount': self.amount,
            'grand_amount': self.grand_amount,
        })

        tmp_sisa_piutang = 0
        for rec in self.line_ids:
            tmp_sisa_piutang += rec.move_id.amount_residual
            
        if tmp_sisa_piutang > 0 and self.amount > tmp_sisa_piutang:
            raise UserError("Angka pembayaran tidak boleh melebihi sisa piutang.\nSisa piutang senilai {piutang}".format(piutang=tmp_sisa_piutang))

        return values

    def _create_payment_vals_from_batch(self, batch_result):
        values = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)

        line_disc = []
        for i in self.payment_line_disc_ids:
            det = [0, False, {
                u'account_id': i.account_id.id,
                u'currency_id': i.currency_id.id,
                u'amount': i.amount,
                u'description': i.description,
            }]
            line_disc.append(det)

        values.update({
            'method_id': self.method_id.id,
            'loa_type': False,
            'no_voucher': self.no_voucher,
            'payment_line_disc_ids': line_disc,
            'amount': self.amount,
            'grand_amount': self.grand_amount,
        })
        return values
    
    def action_create_payments(self):
        payments = self._create_payments()

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })

        # jika dibuat melalui payment requisition
        if self.pr_id:
            # for i in self.pr_id.approval_info_ids:
            #     if not i.is_approve:
            #         i.sudo().write({
            #             'is_approve': True,
            #             'approve_user_id': self.env.user.id,
            #             'approve_date': datetime.now(),
            #         })
            #         break
            self.pr_id.sudo().write({'state': 'approved', 'payment_id': payments.id})
            for activity in self.pr_id.activity_ids:
                activity.sudo().action_feedback(feedback="")

        return action
    
    # @api.model
    # def default_get(self, fields_list):
    #     # OVERRIDE
    #     res = super().default_get(fields_list)

    #     if 'line_ids' in fields_list and 'line_ids' not in res:

    #         # Retrieve moves to pay from the context.

    #         print("self._context.get('active_model') = ", self._context.get('active_model'))

    #         if self._context.get('active_model') == 'account.move' or self._context.get('active_model') == 'account.payment.requisition':
    #             lines = self.env['account.move'].browse(self._context.get('active_ids', [])).line_ids
    #         elif self._context.get('active_model') == 'account.move.line':
    #             lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
    #         else:
    #             raise UserError(_(
    #                 "The register payment wizard should only be called on account.move or account.move.line records."
    #             ))

    #         # Keep lines having a residual amount to pay.
    #         available_lines = self.env['account.move.line']
    #         for line in lines:
    #             if line.move_id.state != 'posted':
    #                 raise UserError(_("You can only register payment for posted journal entries."))

    #             if line.account_internal_type not in ('receivable', 'payable'):
    #                 continue
    #             if line.currency_id:
    #                 if line.currency_id.is_zero(line.amount_residual_currency):
    #                     continue
    #             else:
    #                 if line.company_currency_id.is_zero(line.amount_residual):
    #                     continue
    #             available_lines |= line

    #         # Check.
    #         if not available_lines:
    #             raise UserError(_("You can't register a payment because there is nothing left to pay on the selected journal items."))
    #         if len(lines.company_id) > 1:
    #             raise UserError(_("You can't create payments for entries belonging to different companies."))
    #         if len(set(available_lines.mapped('account_internal_type'))) > 1:
    #             raise UserError(_("You can't register payments for journal items being either all inbound, either all outbound."))

    #         res['line_ids'] = [(6, 0, available_lines.ids)]

    #     return res

    # def _create_payments(self):
    #     self.ensure_one()
    #     batches = self._get_batches()
    #     edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

    #     to_reconcile = []
    #     if edit_mode:
    #         payment_vals = self._create_payment_vals_from_wizard()
    #         payment_vals_list = [payment_vals]
    #         to_reconcile.append(batches[0]['lines'])
    #     else:
    #         # Don't group payments: Create one batch per move.
    #         if not self.group_payment:
    #             new_batches = []
    #             for batch_result in batches:
    #                 for line in batch_result['lines']:
    #                     new_batches.append({
    #                         **batch_result,
    #                         'lines': line,
    #                     })
    #             batches = new_batches

    #         payment_vals_list = []
    #         for batch_result in batches:
    #             payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
    #             to_reconcile.append(batch_result['lines'])

    #     payments = self.env['account.payment'].create(payment_vals_list)

    #     # If payments are made using a currency different than the source one, ensure the balance match exactly in
    #     # order to fully paid the source journal items.
    #     # For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
    #     # If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.

    #     if edit_mode:
    #         for payment, lines in zip(payments, to_reconcile):
    #             # Batches are made using the same currency so making 'lines.currency_id' is ok.
    #             if payment.currency_id != lines.currency_id:
    #                 liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
    #                 source_balance = abs(sum(lines.mapped('amount_residual')))
    #                 payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
    #                 source_balance_converted = abs(source_balance) * payment_rate

    #                 # Translate the balance into the payment currency is order to be able to compare them.
    #                 # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
    #                 # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
    #                 # match.
    #                 payment_balance = abs(sum(counterpart_lines.mapped('balance')))
    #                 payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
    #                 if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
    #                     continue

    #                 delta_balance = source_balance - payment_balance

    #                 # Balance are already the same.
    #                 if self.company_currency_id.is_zero(delta_balance):
    #                     continue

    #                 # Fix the balance but make sure to peek the liquidity and counterpart lines first.
    #                 debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
    #                 credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

    #                 payment.move_id.write({'line_ids': [
    #                     (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
    #                     (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
    #                 ]})

    #     for pay in payments:
    #         if pay.payment_type != 'outbound':
    #             pay.action_post()
    #     # payments.action_post()

    #     domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
    #     for payment, lines in zip(payments, to_reconcile):

    #         # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
    #         # and then, we can't perform the reconciliation.
    #         if payment.state != 'posted':
    #             continue

    #         payment_lines = payment.line_ids.filtered_domain(domain)
    #         for account in payment_lines.account_id:
    #             (payment_lines + lines)\
    #                 .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
    #                 .reconcile()

    #     return payments

class AccountPaymentRegisterDisc(models.TransientModel):
    _name = "account.payment.register.line.disc"

    line_id = fields.Many2one('account.payment.register', string='Disc', index=True, ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="restrict", required=True)    
    currency_id = fields.Many2one('res.currency', string='Currency', related="line_id.currency_id", help="The payment's currency.")
    amount = fields.Monetary(currency_field='currency_id', string='Total', digits='Amount', required=True)
    description = fields.Char(string='Description')