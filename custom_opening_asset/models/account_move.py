from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    correction_id = fields.Many2one('account.asset.correction', string='Correction')
    opening_asset_ids = fields.Many2many('account.asset', string='Opening Assets', domain="[('state', '!=', 'model')]")

    def write(self, vals):
        super(AccountMove, self).write(vals)
        if self.correction_id and not self.env.context.get('bypass'):

            new_vals = {
                'ref': self.ref,
                'date': self.date,
                'journal_id': self.journal_id.id
            }
            if vals.get('line_ids'):
                line_ids = [(5, 0, 0)]
                for line in self.line_ids:
                    line_ids.append((0, 0, {
                        'account_id': line.account_id.id,
                        'partner_id': line.partner_id.id,
                        'name': line.name,
                        'date': line.date,
                        'debit': line.debit,
                        'credit': line.credit
                    }))
                new_vals['line_ids'] = line_ids

            self.correction_id.with_context(bypass=True).update(new_vals)

        return True

    def unlink(self):
        if not self.env.context.get('bypass'):
            if self.correction_id:
                self.correction_id.with_context(bypass=True).unlink()
        return super(AccountMove, self).unlink()

    def open_correction_id(self):
        return {
            'name': self.ref,
            'type': 'ir.actions.act_window',
            'res_model': 'account.asset.correction',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.correction_id.id,
            'target': 'current'
        }

    def action_post(self):
        if self.correction_id:
            self.correction_id.with_context(bypass=True).action_post()
        return super(AccountMove, self).action_post()

    def button_draft(self):
        for move in self:
            if move.asset_id:
                move.asset_id.value_residual -= abs(sum(move.line_ids.filtered(lambda l: l.account_id == move.asset_id.account_depreciation_id and l.parent_state == 'cancel').mapped('balance')))                

        if self.opening_asset_ids:
            raise UserError(_('This move used for asset opening, set to draft assets linked to this move first!'))
        if self.correction_id:
            self.correction_id.with_context(bypass=True).button_draft()
        return super(AccountMove, self).button_draft()

    def button_cancel(self):
        if self.opening_asset_ids:
            raise UserError(_('This move used for asset opening, set to draft assets linked to this move first!'))
        if self.correction_id:
            self.correction_id.with_context(bypass=True).button_cancel()
        return super(AccountMove, self).button_cancel()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    parent_correction_id = fields.Many2one('account.asset.correction', string='Parent Correction', related='move_id.correction_id')
