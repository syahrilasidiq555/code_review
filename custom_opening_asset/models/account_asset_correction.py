from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAssetCorrection(models.Model):
    _name = 'account.asset.correction'
    _description = 'Account Move Asset Correction'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _rec_name = 'ref'

    def _check_balance(self):
        debit = 0.0
        credit = 0.0
        for line in self.line_ids:
            debit += line['debit']
            credit += line['credit']
        if debit != credit:
            raise UserError(_('Total debit and credit must be same!'))
        return True

    def _prepare_move_id(self, correction_id=None):
        correction_id = correction_id or self
        line_ids = []
        for line in correction_id.line_ids:
            line_ids.append(
                (0, 0, {
                    'account_id': line.account_id.id,
                    'partner_id': line.partner_id.id,
                    'name': line.name,
                    'date': line.date,
                    'credit': line.credit,
                    'debit': line.debit
                })
            )

        move_vals = {
            'ref': correction_id.ref,
            'date': correction_id.date,
            'journal_id': correction_id.journal_id.id,
            'correction_id': correction_id.id,
            'line_ids': line_ids,
        }

        return move_vals

    @api.model
    def create(self, vals):
        record = super(AccountAssetCorrection, self).create(vals)

        if vals['create_journal_items']:

            # Create new account.move
            move_vals = self._prepare_move_id(correction_id=record)
            move_id = self.env['account.move'].create(move_vals)
            record.move_id = move_id.id

        self._check_balance()
        return record

    def write(self, vals):
        super(AccountAssetCorrection, self).write(vals)
        self._check_balance()

        if not self.env.context.get('bypass'):
            if self.create_journal_items:
                move_vals = self._prepare_move_id()
                if not self.move_id:
                    move_id = self.env['account.move'].create(move_vals)
                    self.with_context(bypass=True).update({'move_id': move_id.id})
                else:
                    del move_vals['correction_id']
                    if vals.get('line_ids'):
                        move_vals['line_ids'] = [(5, 0, 0)] + move_vals['line_ids']
                    else:
                        del move_vals['line_ids']
                    self.move_id.with_context(bypass=True).update(move_vals)

                if vals.get('state'):
                    if vals['state'] == 'posted':
                        self.move_id.action_post()
                    elif vals['state'] == 'draft':
                        self.move_id.button_draft()
                    elif vals['state'] == 'cancel':
                        self.move_id.button_cancel()
            else:
                if self.move_id:
                    self.move_id.with_context(bypass=True).unlink()
        return True
    
    def unlink(self):
        if not self.env.context.get('bypass'):
            if self.move_id:
                self.move_id.with_context(bypass=True).unlink()
        return super(AccountAssetCorrection, self).unlink()

    def button_draft(self):
        if self.opening_asset_ids:
            raise UserError(_('This move used for asset opening, set to draft assets linked to this move first!'))
        self.write({'state': 'draft'})

    def action_post(self):
        self.write({'state': 'posted'})

    def button_cancel(self):
        if self.opening_asset_ids:
            raise UserError(_('This move used for asset opening, set to draft assets linked to this move first!'))
        self.write({'state': 'cancel'})

    def open_move_id(self):
        return {
            'name': self.ref,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.move_id.id,
            'target': 'current'
        }

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        self._compute_amount_total()

    def _compute_amount_total(self):
        for record in self:
            amount_total = 0.0
            for line in record.line_ids:
                amount_total += line.debit
            record.amount_total = amount_total

    def _compute_move_name(self):
        for record in self:
            if record.move_id:
                record.move_name = record.move_id.name
            else:
                record.move_name = 'Not Created'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)

    ref = fields.Char(string='Correction Name', required=True, tracking=True)
    date = fields.Date(string='Correction Date', required=True,  tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', 'general'), ('company_id', '=', company_id)]", required=True, tracking=True)

    line_ids = fields.One2many('account.asset.correction.line', 'move_id', string='Correction Lines',  tracking=True)
    amount_total = fields.Monetary(string='Amount Total', compute='_compute_amount_total', currency_field='currency_id')

    is_correct_asset = fields.Boolean(string='Correct Asset Value', tracking=True)
    is_correct_depreciation = fields.Boolean(string='Correct Depreciation', tracking=True)
    is_correct_book = fields.Boolean(string='Correct Book Value', tracking=True)

    book_value = fields.Monetary(string='Book Value', currency_id='currency_id', tracking=True)

    move_id = fields.Many2one('account.move', string='Move ID')
    move_name = fields.Char(string='Journal Entries', compute=_compute_move_name)
    asset_model = fields.Many2one('account.asset', string='Asset Model', required=True, tracking=True, domain="[('state', '=', 'model'), ('asset_type', '=', 'purchase')]")
    create_journal_items = fields.Boolean(string='Create Journal Items',  tracking=True)

    opening_asset_ids = fields.Many2many('account.asset', string='Opening Assets', domain="[('state', '!=', 'model'), ('asset_type', '=', 'purchase')]")

    @api.onchange('asset_model')
    def _onchange_asset_model(self):
        if self.asset_model:
            self.journal_id = self.asset_model.journal_id.id


class MoveAssetCorrectionLine(models.Model):
    _name = 'account.asset.correction.line'
    _description = 'Account Move Asset Correction Line'

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for record in self:
            record.balance = record.debit - record.credit

    move_id = fields.Many2one('account.asset.correction', string='Correction', required=True, ondelete='cascade')
    parent_state = fields.Selection(related='move_id.state', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)

    name = fields.Char(string='Label')
    date = fields.Date(string='Date', related='move_id.date')
    account_id = fields.Many2one('account.account', 
        string='Account', 
        required=True, 
        domain="[('company_id', '=', company_id), ('user_type_id.name', 'in', ['Fixed Assets', 'Expenses', 'Aset Tetap', 'Penyusutan', 'Beban Penyusutan', 'Hutang Usaha', 'Beban Pelepasan EDC', 'Pendapatan Beban Lain'])]")
    partner_id = fields.Many2one('res.partner', string='Partner')

    debit = fields.Monetary(string='Debit', currency_field='currency_id')
    credit = fields.Monetary(string='Credit', currency_field='currency_id')
    balance = fields.Monetary(string='Balance', currency_field='currency_id', compute=_compute_balance, store=True)
