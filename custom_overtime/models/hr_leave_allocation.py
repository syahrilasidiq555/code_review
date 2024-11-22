import time
from datetime import datetime


from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    number_of_hours_display = fields.Float(readonly=False)