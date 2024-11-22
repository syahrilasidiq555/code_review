from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

class hr_employee_type(models.Model):
    _name = 'hr.employee.type'
    
    _sql_constraints = [
        (
            'constraint_employee_type_unique_name',
            'unique(name)',
            _('Name already exist.')
        )
    ]
    
    sequence = fields.Integer()
    name = fields.Char(string="Type", tracking=True)
    active = fields.Boolean(default=True)
    jenis_terminasi_ids = fields.Many2many('hr.jenis.terminasi', string='Jenis Terminasi Assign')