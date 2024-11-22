# from attr import field
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    project_id = fields.Many2one('project.project', string='Project')
