# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from datetime import date, datetime

class AccountMove(models.Model):
    _inherit = "account.move"

    # ADD PO, SO, COST SHEET FIELD if exist
    pos_order_id = fields.Many2one('pos.order', string='POS Order', compute="_compute_pos_order_id", store=True)

    @api.depends('invoice_origin')
    def _compute_pos_order_id(self):
        for record in self:
            record.pos_order_id = None

            if record.invoice_origin:
                pos_order = self.env['pos.order'].search([('name','=',record.invoice_origin)], limit=1)

                if pos_order:
                    record.pos_order_id = pos_order[0].id

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pos_line_id = fields.Many2one('pos.order.line', string='POS line')

