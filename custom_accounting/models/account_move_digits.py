# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from datetime import date, datetime

class AccountMove(models.Model):
    _inherit = "account.move"


    amount_untaxed = fields.Monetary(digits="Product Price")
    amount_tax = fields.Monetary(digits="Product Price")
    amount_total = fields.Monetary(digits="Product Price")
    amount_residual = fields.Monetary(digits="Product Price")
    amount_untaxed_signed = fields.Monetary(digits="Product Price")
    amount_tax_signed = fields.Monetary(digits="Product Price")
    amount_total_signed = fields.Monetary(digits="Product Price")
    amount_total_in_currency_signed = fields.Monetary(digits="Product Price")
    amount_residual_signed = fields.Monetary(digits="Product Price")