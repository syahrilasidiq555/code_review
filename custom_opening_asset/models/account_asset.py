from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    # INHERITED/OVERRIDDEN FUNCTION
    # ---------------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if self.env.company.compute_asset_based_opening and not self.env.company.account_opening_move_id:
            raise ValidationError(_('You must define your opening balance first!'))
        return super(AccountAsset, self).create(vals)

    @api.onchange('account_depreciation_id')
    def _onchange_account_depreciation_id(self):
        super(AccountAsset, self)._onchange_account_depreciation_id()

        asset_types = self.mapped('asset_type')

        all_purchases = False
        if len(set(asset_types)) == 1:
            if list(set(asset_types))[0] == 'purchase':
                all_purchases = True

        if self.env.company.compute_asset_based_opening and all_purchases:
            self._compute_amount_opening()

    def _set_value(self):
        # super(AccountAsset, self)._set_value()
        asset_types = self.mapped('asset_type')

        all_purchases = False
        if len(set(asset_types)) == 1:
            if list(set(asset_types))[0] == 'purchase':
                all_purchases = True

        if self.env.company.compute_asset_based_opening and all_purchases:
            self._compute_amount_opening()

    def set_to_draft(self):
        asset_types = self.mapped('asset_type')

        all_purchases = False
        if len(set(asset_types)) == 1:
            if list(set(asset_types))[0] == 'purchase':
                all_purchases = True

        if self.env.company.compute_asset_based_opening and all_purchases:
            for record in self:
                super(AccountAsset, record).set_to_draft()
                record._set_value()
                record.move_opening_ids = [(5, 0, 0)]
                record.correction_opening_ids = [(5, 0, 0)]
        else:
            super(AccountAsset, self).set_to_draft()

    # We need to override this method, because it's return the direct write function
    def compute_depreciation_board(self):
        self.ensure_one()
        amount_change_ids = self.depreciation_move_ids.filtered(lambda x: x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
        already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
        depreciation_number = self.method_number
        if self.prorata:
            depreciation_number += 1
        starting_sequence = 0
        amount_to_depreciate = self.value_residual + sum([m.amount_total for m in amount_change_ids])
        depreciation_date = self.first_depreciation_date
        # if we already have some previous validated entries, starting date is last entry + method period
        if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].date:
            last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
            if last_depreciation_date > depreciation_date:  # in case we unpause the asset
                depreciation_date = last_depreciation_date + relativedelta(months=+int(self.method_period))
        commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state == 'draft')]
        newlines = self._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids)
        newline_vals_list = []
        for newline_vals in newlines:

            # Change only apply on this line to prevent old entries created
            if self.compute_asset_based_opening and self.asset_type == 'purchase' and newline_vals['date'] < self.env.company.account_opening_date:
                continue

            # no need of amount field, as it is computed and we don't want to trigger its inverse function
            del(newline_vals['amount_total'])
            newline_vals_list.append(newline_vals)
        new_moves = self.env['account.move'].create(newline_vals_list)
        for move in new_moves:
            commands.append((4, move.id))
        return self.write({'depreciation_move_ids': commands})

    def validate(self):

        asset_types = list(set(self.mapped('asset_type')))
        if len(asset_types) != 1:
            raise ValidationError(_("Can't run for different types!"))

        if asset_types[0] != 'purchase':
            super(AccountAsset, self).validate()
            for asset in self:
                # re-write auto_post entries based options
                asset.depreciation_move_ids.write({'auto_post': False})
            return

        if not self.env.company.compute_asset_based_opening:
            super(AccountAsset, self).validate()
            for asset in self:
                # re-write auto_post entries based options
                asset.depreciation_move_ids.write({'auto_post': False})
            return

        date_before = False
        date_after = False
        for date in list(set(self.mapped('first_depreciation_date'))):
            if date < self.env.company.account_opening_date:
                date_before = True
            else:
                date_after = True
            if date_before and date_after:
                raise ValidationError(_("Some assets has first depreciation date > opening and some assets don't!"))

        # If assets computed based opening, match their opening amount
        # Check if asset is forced to run
        if not self.env.context.get('ignore_check'):
            action = self.check_amount_opening()

            # if there's an action (means opening amount doesn't match, then display wizard)
            if action:
                return action

        # Call the main function
        super(AccountAsset, self).validate()
        for asset in self:
            # re-write auto_post entries based options
            asset.depreciation_move_ids.write({'auto_post': self.env.context.get('auto_post')})

            # since some journal entries are not created,
            # we must decrease their book and residual value

            amount_already_deprec = asset.amount_opening - sum(asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted').mapped('amount_total'))

            asset.book_value += amount_already_deprec
            asset.value_residual += amount_already_deprec

    # NEW CREATED FUNCTION
    # ---------------------------------------------------------------------------------
    @api.onchange('first_depreciation_date')
    def _onchange_first_depreciation_date(self):
        if self.compute_asset_based_opening and self.asset_type == 'purchase':
            self._compute_amount_opening()

    # This method is a copy of compute_depreciation_board method
    # but with assets initial values
    def _compute_amount_opening(self):
        for record in self:
            if not record.compute_asset_based_opening or not record.asset_type == 'purchase':
                record.amount_opening = 0.0
                continue

            depreciation_number = record.method_number if not record.prorata else record.method_number + 1
            starting_sequence = 0
            amount_to_depreciate = record.original_value - record.salvage_value
            depreciation_date = record.first_depreciation_date
            already_depreciated_amount = 0
            amount_change_ids = False

            newlines = record._recompute_board(
                depreciation_number,
                starting_sequence,
                amount_to_depreciate,
                depreciation_date,
                already_depreciated_amount,
                amount_change_ids
            )

            # Filter only entries with date >= opening date will be count
            amount_opening = 0.0
            for newline_vals in newlines:
                if newline_vals['date'] < record.env.company.account_opening_date:
                    amount_opening += newline_vals['amount_total']
            record.amount_opening = -amount_opening

    def _get_calculated_opening_balance(self, account_depreciation_id):

        # Calculate the exact opening balance for the asset
        calculated_opening = self.search([
            ('first_depreciation_date', '<', self.env.company.account_opening_date),
            ('account_depreciation_id', '=', account_depreciation_id.id)
        ])

        # Check if any correction has been made before opening
        correction_lines = self.env['account.asset.correction.line'].search([
            ('parent_state', '=', 'posted'),
            ('account_id', '=', account_depreciation_id.id),
            ('date', '<', self.env.company.account_opening_date)
        ])

        # Check if any move has been made before opening
        move_lines = self.env['account.move.line'].search([
            ('parent_state', '=', 'posted'),
            ('parent_correction_id', '=', False),
            ('account_id', '=', account_depreciation_id.id),
            ('date', '<', self.env.company.account_opening_date),
        ])

        inputted_opening = self.env['account.move.line'].search([
            ('move_id', '=', self.env.company.account_opening_move_id.id),
            ('account_id', '=', account_depreciation_id.id)
        ])

        return calculated_opening, inputted_opening, move_lines, correction_lines

    def check_amount_opening(self):

        model_id = self.mapped('model_id')[0]
        currency_id = self.mapped('currency_id')[0]
        account_depreciation_id = self.mapped('account_depreciation_id')[0]
        account_depreciation_expense_id = self.mapped('account_depreciation_expense_id')[0]

        calculated_opening, inputted_opening, move_lines, correction_lines = self._get_calculated_opening_balance(account_depreciation_id)

        calculated_balance = sum(calculated_opening.mapped('amount_opening'))
        opening_balance = sum(inputted_opening.mapped('balance'))
        correction_balance = sum(correction_lines.mapped('balance')) + sum(move_lines.mapped('balance'))

        if abs((calculated_balance + correction_balance) - opening_balance) < abs((opening_balance + correction_balance) - calculated_balance):
            calculated_balance = calculated_balance + correction_balance
        else:
            opening_balance = opening_balance + correction_balance

        move_opening = move_lines.mapped('move_id')
        correction_opening = correction_lines.mapped('move_id')

        if currency_id.compare_amounts(opening_balance, calculated_balance):
            values = {
                'opening_balance': opening_balance,
                'move_ids': [(4, move.id) for move in move_opening],
                'correction_ids': [(4, move.id) for move in correction_opening],
                'calculated_balance': calculated_balance,
                'asset_model': model_id.id,
                'account_counter_id': account_depreciation_expense_id.id,
                'date': self.env.company.account_opening_date - relativedelta(days=1)
            }

            confirm_id = self.env['account.asset.validate.confirm'].create(values)
            return {
                'name': 'Warning!',
                'type': 'ir.actions.act_window',
                'res_model': 'account.asset.validate.confirm',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': confirm_id.id,
                'context': {'active_model': 'account.asset', 'active_ids': self.ids},
                'target': 'new'
            }

        asset_ids = []
        for record in self:
            if record.first_depreciation_date < self.env.company.account_opening_date:
                record.update({
                    'move_opening_ids': [(4, move.id) for move in move_opening],
                    'correction_opening_ids': [(4, move.id) for move in correction_opening]
                })
                asset_ids.append(record.id)

        move_opening.update({'opening_asset_ids': [(4, asset_id) for asset_id in asset_ids]})
        correction_opening.update({'opening_asset_ids': [(4, asset_id) for asset_id in asset_ids]})

    def action_check(self):
        # Check if there's different state and asset models
        context = self.env.context
        self.with_context(context)._check_action_validation(valid_state=context.get('valid_state'))

        if context.get('validate'):
            return self.with_context(context).validate()
        elif context.get('set_draft'):
            return self.with_context(context).set_to_draft()
        else:
            raise ValidationError(_('No context detected for this action!'))

    def _check_action_validation(self, valid_state):

        # Check asset states
        asset_states = sorted(set(self.mapped('state')))
        if len(asset_states) > 1:
            raise ValidationError(_('Cannot run action for asset that has different status!'))
        elif len(asset_states) == 1:
            if asset_states[0] != valid_state:
                raise ValidationError(_(f'Cannot run action for {asset_states[0]} assets!'))

        # Check asset models
        has_no_model = any([True if not asset.model_id else False for asset in self])
        if has_no_model:
            raise ValidationError(_('Cannot run action for asset that has no model!'))
        elif len(self.mapped('model_id')) > 1:
            raise ValidationError(_('Cannot run action for asset that has different models!'))

        # Check asset accounts
        account_asset_ids = self.mapped('account_asset_id')
        account_depreciation_ids = self.mapped('account_depreciation_id')
        account_depreciation_expense_ids = self.mapped('account_depreciation_expense_id')
        if any([len(accounts) != 1 for accounts in [account_asset_ids, account_depreciation_ids, account_depreciation_expense_ids]]):
            raise ValidationError(_('Cannot run action with different accounts!'))

    model_id = fields.Many2one('account.asset', string='Model', 
        change_default=True, 
        readonly=True, states={'draft': [('readonly', False)]}, 
        domain="[('company_id', '=', company_id), ('state', '=', 'model')]")
    amount_opening = fields.Monetary(string='Opening Amount', currency_field='currency_id', compute=_compute_amount_opening)
    compute_asset_based_opening = fields.Boolean(related='company_id.compute_asset_based_opening', string='Compute Asset based Opening')
    move_opening_ids = fields.Many2many('account.move', string='Opening Journal Entries', domain="[('move_type', '=', 'entry')]")
    correction_opening_ids = fields.Many2many('account.asset.correction', string='Opening Corrections')
