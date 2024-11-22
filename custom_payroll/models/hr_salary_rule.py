from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    appears_on_correction = fields.Boolean(string='Appears on Correction', default=False,
        help="Used to display the salary rule on Correction.")
    appears_on_premi = fields.Boolean(string='Appears on Premi', default=False,
        help="Used to display the salary rule on Premi.")