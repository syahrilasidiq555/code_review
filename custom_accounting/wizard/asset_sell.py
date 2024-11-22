# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class AssetSell(models.TransientModel):
    _inherit = 'account.asset.sell'

    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='restrict')
    kronologi = fields.Html(string='Kronologi')
    dispose_date = fields.Date(string='Dispose Date', default=fields.Datetime.now)

    def do_action(self):
        if self.action == 'dispose':
            self.asset_id.write({
                'state':'to_approve_dispose',
                'employee_id':self.employee_id.id,
                'kronologi':self.kronologi,
                'dispose_date':self.dispose_date,
                })
            return
        else:
            self.ensure_one()
            invoice_line = self.env['account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
            return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)