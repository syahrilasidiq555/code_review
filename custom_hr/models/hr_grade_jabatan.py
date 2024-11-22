from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

class hr_job_grade(models.Model):
    _name = 'hr.job.grade'

    _sql_constraints = [
        ("name_check", "check(name)", "Name already exist."),
    ]
    name = fields.Char(string="Grade", tracking=True)
    active = fields.Boolean(default="True", tracking=True)