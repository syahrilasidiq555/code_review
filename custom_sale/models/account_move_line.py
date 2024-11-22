from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    rel_curr_rate = fields.Float(compute='_compute_rel_curr_rate', store=True)
    
    @api.depends('currency_rate','currency_id', 'company_id', 'move_id.date')
    def _compute_rel_curr_rate(self):
        for record in self:
            record.rel_curr_rate = 1
            if record.currency_rate:
                record.rel_curr_rate = record.currency_rate
