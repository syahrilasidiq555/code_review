from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from num2words import num2words

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # kebutuhan readonly payment type
    def _default_payment_fix(self):
        return self.env.context.get('readonly_payment_type')

    payment_fix = fields.Boolean(default=_default_payment_fix, compute="_compute_payment_fix")
    @api.depends()
    def _compute_payment_fix(self):
        for rec in self:
            rec.payment_fix = self.env.context.get('readonly_payment_type')

    # kebutuhan columbarium
    sale_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    is_columbarium = fields.Boolean(default=False)

    tax_ids = fields.Many2many('account.tax', string='Taxes', tracking=True)
    no_voucher = fields.Char(string="Voucher", tracking=True)
    method_id = fields.Many2one('payment.method', string="Payment Method", required=False)
    grand_amount = fields.Monetary(currency_field='currency_id', compute="_compute_grand_amount", store=True, tracking=True)

    @api.onchange('method_id')
    def _onchange_method_id(self):
        if self.method_id:
            self.journal_id = self.method_id.journal_id

    @api.depends('amount', 'payment_line_disc_ids')
    def _compute_grand_amount(self):
        for rec in self:
            rec.grand_amount = rec.amount - sum(rec.payment_line_disc_ids.mapped('amount'))

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_amount_currency = 0 #write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.grand_amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.grand_amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # untuk potongan
        if self.payment_line_disc_ids:
            discount_balance = self.currency_id._convert(
                sum(self.payment_line_disc_ids.mapped('amount')),
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            if self.payment_type == 'inbound':
                counterpart_amount_currency -= sum(self.payment_line_disc_ids.mapped('amount'))
                counterpart_balance -= discount_balance
            elif self.payment_type == 'outbound':
                counterpart_amount_currency += sum(self.payment_line_disc_ids.mapped('amount'))
                counterpart_balance += discount_balance
                # liquidity_amount_currency += sum(self.payment_line_disc_ids.mapped('amount'))
                # liquidity_balance += discount_balance

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = self._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        if self.payment_mode == "others":
            tot_header = 0
            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                    # 'no_voucher': self.no_voucher,
                },
            ]

            for i in self.payment_line_ids:
                if self.payment_type == 'inbound':
                    line_balance = -i.amount
                elif self.payment_type == 'outbound':
                    line_balance = i.amount
                else:
                    line_balance = i.amount
                line_amount = i.currency_id._convert(
                    line_balance,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                values = {
                    'name': i.description,
                    'date_maturity': self.date,
                    'amount_currency': line_balance,
                    'currency_id': i.currency_id.id,
                    'debit': line_amount if line_amount > 0.0 else 0.0,
                    'credit': -line_amount if line_amount < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': i.account_id.id,
                    # 'no_voucher': self.no_voucher,
                }
                tot_header += line_amount
                line_vals_list.append(values)

            if self.currency_id.id != self.env.company.currency_id.id:
                for i in line_vals_list:
                    if i['account_id'] == self.outstanding_account_id.id:
                        if i['debit'] > 0:
                            i['debit'] = tot_header if tot_header > 0 else tot_header * -1
                        elif i['credit'] > 0:
                            i['credit'] = tot_header if tot_header > 0 else tot_header * -1
        else:
            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                    # 'no_voucher': self.no_voucher,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                    # 'no_voucher': self.no_voucher,
                },
            ]

        account_tax_amount = {}
        for tax in self.tax_ids:
            tax_ids = []
            if tax.amount_type == 'group':
                for tax_child in tax.children_tax_ids:
                    tax_ids.append(tax_child.id or tax_child._origin.id)
            else:
                tax_ids.append(tax.id or tax._origin.id)

            repartition_line_ids = self.env['account.tax.repartition.line'].search([
                ('payment_tax_id', 'in', tax_ids)
            ])

            for repr_line in repartition_line_ids:
                if repr_line.repartition_type == 'base':
                    continue

                tax_id = repr_line.payment_tax_id
                if repr_line.account_id:
                    if tax_id.amount_type == 'percent':
                        amount = (self.amount * ((tax_id.amount * repr_line.factor_percent) / 100)) / 100
                        # amount = (self.amount * ((tax_id.amount * repr_line.factor_percent) / 100)) / 100
                    elif tax_id.amount_type == 'fixed':
                        amount = (tax_id.amount * repr_line.factor_percent) / 100
                    else:
                        amount = (self.amount * ((tax_id.amount * repr_line.factor_percent) / 100)) / 100
                        # amount = (self.amount * ((tax_id.amount * repr_line.factor_percent) / 100)) / 100

                    key = f"{repr_line.account_id.id}_{self.partner_id.commercial_partner_id.id}_{tax_id.id}_{repr_line.id}"
                    if key not in account_tax_amount:
                        account_tax_amount[key] = amount
                    else:
                        account_tax_amount[key] += amount

        total_amount = 0.0
        if account_tax_amount:
            for key, balance in account_tax_amount.items():
                account_id, partner_id, tax_id, repr_id = key.split('_')
                tax_name = self.env['account.tax'].browse(eval(tax_id))[0].description

                balance_tax = self.currency_id._convert(
                    balance,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                balance_tax = -balance_tax if self.payment_type == 'outbound' else balance_tax

                values = {
                    'name': tax_name,
                    'date_maturity': self.date,
                    'amount_currency': currency_id and balance or 0.0,
                    'currency_id': currency_id,
                    'debit': balance_tax < 0 and -balance_tax or 0.0,
                    'credit': balance_tax > 0 and balance_tax or 0.0,
                    'partner_id': eval(partner_id),
                    'account_id': eval(account_id),
                    # 'no_voucher': self.no_voucher,
                }
                total_amount += balance
                line_vals_list.append(values)

        # di komen saja, karna menyebabkan double2 data ketika edit
        # if self.payment_mode != "others":
        #     if not self.currency_id.is_zero(write_off_amount_currency):
        #         # Write-off line.
        #         line_vals_list.append({
        #             'name': write_off_line_vals.get('name') or default_line_name,
        #             'amount_currency': write_off_amount_currency,
        #             'currency_id': currency_id,
        #             'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
        #             'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
        #             'partner_id': self.partner_id.id,
        #             'account_id': write_off_line_vals.get('account_id'),
        #         })
        
        # untuk potongan
        if self.payment_line_disc_ids:
            for i in self.payment_line_disc_ids:
                # print("i.account_id.name = ", i.account_id.name)
                balance_disc = i.currency_id._convert(
                    i.amount,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )

                if self.payment_type == 'inbound':
                    balance_disc = balance_disc
                else:
                    balance_disc = -balance_disc

                values = {
                    'name': i.description,
                    'date_maturity': self.date,
                    'amount_currency': currency_id and i.amount or 0.0, #currency_id and balance_disc or 0.0,
                    'currency_id': currency_id,
                    'debit': balance_disc if balance_disc > 0.0 else 0.0,
                    'credit': -balance_disc if balance_disc < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': i.account_id.id,
                    # 'no_voucher': self.no_voucher,
                }
                line_vals_list.append(values)
        
        return line_vals_list
    
    @api.onchange('payment_line_ids')
    def _onchange_payment_line_ids(self):
        for rec in self:
            if rec.payment_mode == 'others':
                rec.amount = sum(rec.payment_line_ids.mapped('amount'))

    @api.onchange('is_internal_transfer')
    def _onchange_is_internal_transfer_inherit(self):
        self.payment_line_ids = False
        self.payment_line_disc_ids = False
        self.payment_mode = 'on_payment'
        self.loa_type = False

    payment_line_ids = fields.One2many('account.payment.line', 'line_id', string='Line', copy=True)
    payment_line_disc_ids = fields.One2many('account.payment.line.disc', 'line_id', string='Disc')
    payment_mode = fields.Selection([
        ("on_payment", "On Payment"),
        ("others", "Others"),
    ], default='on_payment', string="Payment Mode")
    criteria_type = fields.Selection([
        ("biaya", "Biaya"),
        ("lain-lain", "Lain-lain"),
        ('columnbarium','Columbarium')
    ], string="Criteria Type")
    
    @api.onchange('payment_mode','payment_type')
    def _onchange_payment_mode(self):
        if self.payment_mode == 'others':
            if self.payment_type == 'outbound':
                self.criteria_type = 'biaya'
            elif self.payment_type == 'inbound':
                self.criteria_type = 'lain-lain'
    
    @api.depends('recuring_duration','recuring_master_id')
    def _compute_recuring_text(self):
        for rec in self:
            rec.recuring_text = str(rec.recuring_duration) + " Month"

    @api.constrains('payment_line_ids')
    def _constrains_payment_line_ids(self):
        for rec in self:
            if rec.payment_mode == 'others' and not rec.payment_line_ids:
                raise ValidationError(_("Nothing to create %s Payments",self.get_criteria_text(rec.criteria_type)))

    def get_criteria_text(self, criteria):
        criteria_list = {
            'transfer': "Transfer",
            'petty_cash': "Petty Cash",
            'cash_advance': "Cash Advance",
        }
        return criteria_list.get(criteria, "nothing")

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, "
                #         "all optional journal items must share the same account.",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))

                if counterpart_lines[0].account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency
                writeoff_amount = sum(writeoff_lines.mapped("amount_currency"))
                disc_amount = sum(pay.payment_line_disc_ids.mapped("amount"))

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount + writeoff_amount) if disc_amount != 0 else abs(liquidity_amount) + abs(writeoff_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id if len(counterpart_lines.account_id) == 1 else False,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            if pay.payment_mode != "others":            
                pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        # if not any(field_name in changed_fields for field_name in (
        #     'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
        #     'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'payment_line_ids', 'payment_line_disc_ids'
        # )):
        #     return

        for pay in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.

            if writeoff_lines:
                counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                # To be consistent with the payment_difference made in account.payment.register,
                # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                # Since the write is already done at this point, we need to base the computation on accounting values.
                if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                    sign = -1
                else:
                    sign = 1
                writeoff_amount = abs(writeoff_amount) * sign

                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}

            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

            # import pprint
            # pprint.pprint(liquidity_lines)
            # pprint.pprint(line_vals_list)
            # pprint.pprint(writeoff_lines)

            # if self.payment_mode == "others":
            if liquidity_lines:
                line_ids_commands = [
                    (1, liquidity_lines.id, line_vals_list[0]),
                ]
            else:
                line_ids_commands = [
                    (0, 0, line_vals_list[0]),
                ]

            # REMOVE EXISTING LINE
            for line in writeoff_lines:
                line_ids_commands.append((3, line.id))
            for line in counterpart_lines:
                line_ids_commands.append((3, line.id))
            # -------------

            for extra_line_vals in line_vals_list[1:]:
                line_ids_commands.append((0, 0, extra_line_vals))

            # else:
            #     line_ids_commands = [
            #         (1, liquidity_lines.id, line_vals_list[0]),
            #         (1, counterpart_lines.id, line_vals_list[1]),
            #     ]

            #     for line in writeoff_lines:
            #         line_ids_commands.append((2, line.id))

            #     for extra_line_vals in line_vals_list[2:]:
            #         line_ids_commands.append((0, 0, extra_line_vals))

            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.
            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            })

    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:

            paired_payment = payment.copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                'move_id': None,
                'ref': payment.ref,
                'paired_internal_transfer_payment_id': payment.id,
                'amount':payment.amount,
                'date': payment.date,
            })
            paired_payment.move_id._post(soft=False)
            payment.paired_internal_transfer_payment_id = paired_payment

            body = _('This payment has been created from <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (payment.id, payment.name)
            paired_payment.message_post(body=body)
            body = _('A second payment has been created: <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (paired_payment.id, paired_payment.name)
            payment.message_post(body=body)

            lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            lines.reconcile()

    @api.depends('amount_total_signed', 'payment_type')
    def _compute_amount_company_currency_signed(self):
        for payment in self:
            if payment.payment_mode == 'others':
                if payment.payment_type == 'outbound':
                    payment.amount_company_currency_signed = -payment.amount
                else:
                    payment.amount_company_currency_signed = payment.amount
            else:
                if payment.payment_type == 'outbound':
                    payment.amount_company_currency_signed = -payment.amount_total_signed
                else:
                    payment.amount_company_currency_signed = payment.amount_total_signed     

    def prepare_vals(self, pembayaran, add_month, payment_line_ids):
        # pemb_rec = self.env['account.payment'].search([('id', '=', pembayaran.id)])
        vals = {
            'amount': pembayaran.amount,
            'criteria_type': pembayaran.criteria_type,
            'currency_id': pembayaran.currency_id.id,
            'date': pembayaran.date + relativedelta(months = add_month),
            'destination_journal_id': pembayaran.destination_journal_id.id,
            'edi_document_ids': pembayaran.edi_document_ids.ids,
            'is_internal_transfer': pembayaran.is_internal_transfer,
            'journal_id': pembayaran.journal_id.id,
            'no_voucher': pembayaran.no_voucher,
            'paired_internal_transfer_payment_id': pembayaran.paired_internal_transfer_payment_id.id,
            'partner_id': pembayaran.partner_id.id,
            'partner_type': pembayaran.partner_type,
            'payment_line_ids': payment_line_ids,
            'payment_method_line_id': pembayaran.payment_method_line_id.id,
            'payment_mode': pembayaran.payment_mode,
            'payment_token_id': pembayaran.payment_token_id.id,
            'payment_type': pembayaran.payment_type,
            'posted_before': pembayaran.posted_before,
            'recuring_duration': 0,
            'recuring_master_id': pembayaran.id,
            'ref': pembayaran.ref,
            'tax_ids': pembayaran.tax_ids.ids,
            }
        return vals

    def recuring_payments(self, pembayaran, durations):
        for duration in range(durations):
            line_ids = []
            if pembayaran.payment_line_ids:
                for i in pembayaran.payment_line_ids:
                    line_ids.append([0,0,{
                        # 'line_id':i.line_id.id,
                        'account_id':i.account_id.id,
                        'currency_id':i.currency_id.id,
                        'amount':i.amount,
                        'description':i.description,
                    }])
                    
            pemb_rec = self.env['account.payment']
            vals = pemb_rec.prepare_vals(pembayaran, duration + 1, line_ids)
            result = pemb_rec.create(vals)
        return

    # Kebutuhan Approval
    loa_type = fields.Many2one('level.approval', string='Approval Type', 
        domain=[('model_id.model', '=', 'account.payment')], default=False)
    approval_info_ids = fields.Many2many('approval.info','payment_approval_line','payment_id','approval_id', 
                                         string='Approval Information', store=True)
    next_approve_user_id = fields.Many2one('res.users', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_request_approval = fields.Boolean(compute='_get_current_user')
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    is_amount = fields.Boolean(string="Range Amount", store=True)
    from_amount = fields.Float(string='From Amount', store=True)
    to_amount = fields.Float(string='To Amount', store=True)
    state_approve = fields.Selection(
        string='State Approve',
        selection=[('draft', 'Draft'), ('to approve', 'To Approve'), ('approved','Approved')],
        default='draft',
        tracking=True
    )

    @api.constrains('loa_type')
    def _check_loa_type(self):
        for rec in self:
            if rec.payment_type == 'outbound' and rec.amount >= 1000000 and not rec.loa_type:
                pass
                # sementara di komen
                # nanti akan ada perubahan flow dari payment requisition
                # raise ValidationError("Approval Type harus dipilih, karena amount sudah melebihi 1.000.000")

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.is_user_approve_now = False
            if rec.next_approve_user_id:
                rec.is_user_approve_now = rec.state_approve == 'to approve' and rec.next_approve_user_id == self.env.user
            rec.is_request_approval = rec.loa_type and rec.state == 'draft' and rec.create_uid == self.env.user
    
    @api.onchange('loa_type')
    def _onchange_loa_type(self):
        for rec in self:
            if rec.payment_type == 'outbound': # and rec.amount >= 1000000:
                app_inf = []
                rec.approval_info_ids = False
                if rec.loa_type:
                    if rec.loa_type.is_amount:
                        if rec.amount_total >= rec.loa_type.from_amount and rec.amount_total <= rec.loa_type.to_amount:
                            rec.is_amount = rec.loa_type.is_amount
                            rec.from_amount = rec.loa_type.from_amount
                            rec.to_amount = rec.loa_type.to_amount
                        else:
                            raise ValidationError("Total Order tidak sesuai dengan range amount pada Approval Type")
                    dtLine = self.env['level.approval.line'].search([('loa_id','=',rec.loa_type.id)], order='sequence asc')
                    for i in dtLine:
                        tmp = [0,0,{
                            'sequence': i.sequence,
                            'loa_id': i.loa_id.id,
                            'model_id': self.loa_type.model_id.id,
                            'trx_id': False,
                            'description': i.description,
                            'user_id': i.user_id.id,
                            'is_approve': False,
                            'approve_user_id': False,
                            'approve_date': False,
                            'approver_sign': False,
                        }]
                        app_inf.append(tmp)
                rec.approval_info_ids = app_inf
            else:
                rec.approval_info_ids = False

    @api.depends('amount')
    @api.onchange('amount')
    def _onchange_amount_total_approval_type(self):
        if self.payment_type == 'outbound' and not self.is_internal_transfer: # and self.amount >= 1000000:
            dtApprvl = self.env['level.approval'].search([('model_id.model', '=', 'account.payment'),('from_amount','<=',self.amount_total),('to_amount','>=',self.amount_total)], limit=1)
            # print("dtApprvl = ", dtApprvl)
            if dtApprvl:
                self.loa_type = dtApprvl.id
            else:
                dtApprvl = self.env['level.approval'].search([('model_id.model', '=', 'account.payment')], limit=1)
                if dtApprvl:
                    self.loa_type = dtApprvl.id
        else:
            self.loa_type = False

    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            if rec.payment_type == 'outbound' and rec.loa_type: #and rec.amount >= 1000000
                rec.next_approve_user_id = False
                if rec.approval_info_ids and rec.state_approve in ['to approve','draft']:
                    for i in rec.approval_info_ids:
                        if not i.is_approve:
                            rec.next_approve_user_id = i.user_id.id
                            break
            else:
                rec.next_approve_user_id = False

    def send_schedule_actifity(self):
        if self.state_approve == 'to approve':
            todos = {
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'account.payment')]).id,
                'user_id': self.next_approve_user_id.id,
                'summary': 'Request Approval',
                'note': 'Hi. Please approve this order',
                'activity_type_id': 4,
                'date_deadline': datetime.now(),
            }
            self.env['mail.activity'].sudo().create(todos)

    def updateTrxId(self):
        for rec in self:
            for i in rec.approval_info_ids:
                i.write({'trx_id':rec.id})

    def button_approve(self, force=False):
        maxSeq = None if not self.loa_type else max(self.approval_info_ids.mapped('sequence'))
        lastApprove = True if not self.loa_type else False

        if self.approval_info_ids and self.state_approve == 'to approve':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    i.write({
                        'is_approve': True,
                        'approve_user_id': self.env.user.id,
                        'approve_date': datetime.now(),
                    })
                    lastApprove = i.sequence == maxSeq
                    break

        if lastApprove:
            self.write({'state_approve': 'approved'})
            self.action_post()

        for activity in self.activity_ids:
            activity.action_feedback(feedback="")

        if not lastApprove:
            self.send_schedule_actifity()

        return {}
    
    def action_to_approve(self):
        self.sudo().write({'state_approve':'to approve'})
        self.send_schedule_actifity()

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        self.sudo().write({'state_approve':'draft'})
        for rec in self.approval_info_ids:
            rec.sudo().write({'is_approve': False, 'approve_user_id': False, 'approve_date': False})
        return res

    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        self.sudo().write({'state_approve':'draft'})
        for rec in self.approval_info_ids:
            rec.sudo().write({'is_approve': False, 'approve_user_id': False, 'approve_date': False})
        return res

    #------------------------------------------------------------

    def _format_currency(self, value=None, separator='.', p2w=False):
        value = self.amount_untaxed if not value and value != 0.0 else value
        value = int(value) if int(value) == value else value
        if not p2w:
            value = '{:,}'.format(value).replace('.', '_comma_')
            value = value.replace(',', separator)
            return value.replace('_comma_', ',')
        return num2words(value, lang='id', to='currency').title()

    def button_open_invoices(self):
        action = super(AccountPayment, self).button_open_invoices()
        action['context'] = {
            'create': False,
            'default_move_type': 'out_invoice'
        }
        return action

    def button_open_bills(self):
        action = super(AccountPayment, self).button_open_bills()
        action['context'] = {
            'create': False,
            'default_move_type': 'in_invoice'
        }
        return action
    
    @api.model_create_multi
    def create(self, vals_list):
        import pprint
        pprint.pprint(vals_list)
        for vals in vals_list:
            if 'is_internal_transfer' in vals:
                if vals['is_internal_transfer'] == True:
                    vals['loa_type'] = False

        payments = super().create(vals_list)
        for i, pay in enumerate(payments):
            if not pay.ref:
                pay.move_id.write({'ref': pay.get_criteria_text(pay.criteria_type)})

        for vals in vals_list:
            if 'approval_info_ids' in vals:
                payments.updateTrxId()

        return payments

    def write(self, vals):
        payments = super().write(vals)
        return payments

class AccountPaymentLine(models.Model):
    _name = "account.payment.line"

    line_id = fields.Many2one('account.payment', string='Payment', index=True, ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="restrict", required=True)    
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, related="line_id.currency_id", help="The payment's currency.")
    amount = fields.Monetary(currency_field='currency_id', string='Total', digits='Amount', required=True)
    description = fields.Char(string='Description')

class AccountPaymentLineDisc(models.Model):
    _name = "account.payment.line.disc"

    line_id = fields.Many2one('account.payment', string='Payment', index=True, ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="restrict", required=True)    
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, related="line_id.currency_id", help="The payment's currency.")
    amount = fields.Monetary(currency_field='currency_id', string='Total', digits='Amount', required=True)
    description = fields.Char(string='Description')

