from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta, date

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    criteria_type = fields.Selection(selection_add=[('cash_advance', 'Cash Advance')])