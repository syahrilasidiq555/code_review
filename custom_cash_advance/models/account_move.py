# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from datetime import date, datetime

class AccountMove(models.Model):
    _inherit = "account.move"

    # ADD PO, SO, COST SHEET FIELD if exist
    cash_advance_id = fields.Many2one('cash.advance', string='Cash Advance', compute="_compute_cash_advance_id", store=True)

    @api.depends('invoice_origin')
    def _compute_cash_advance_id(self):
        for record in self:
            record.cash_advance_id = None

            if record.invoice_origin:
                pos_order = self.env['cash.advance'].search([('name','=',record.invoice_origin)], limit=1)

                if pos_order:
                    record.cash_advance_id = pos_order[0].id