# from attr import field
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

class crm_stage(models.Model):
    _inherit = "crm.stage"

    is_lost = fields.Boolean('Is Lost Stage?')

    @api.constrains('is_lost','is_won')
    def _constrains_is_lost_won(self):
        for record in self:
            if record.is_lost and record.is_won:
                raise ValidationError("Cannot checked LOST and WON stage in the same record!")