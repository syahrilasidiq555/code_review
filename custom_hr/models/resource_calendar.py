# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    is_shift_3 = fields.Boolean('Is Shift 3 Working Times?')