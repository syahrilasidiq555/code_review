from odoo import models, fields, api
from odoo.tools import OrderedSet
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

class stockMove(models.Model):
    _inherit = 'stock.move'

    partner_id = fields.Many2one(store=True)

    def _action_done(self, cancel_backorder=False):
        res = super(stockMove, self)._action_done(cancel_backorder=cancel_backorder)
        if self.picking_id.date_done:
            res.write({'state': 'done', 'date': self.picking_id.date_done})
        return res
    
    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        res = super(stockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        res['date'] = self.picking_id.date_done
        return res
    
    @api.model
    def create(self, vals):
        res = super(stockMove, self).create(vals)
        return res