# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError


class hr_department(models.Model):
    _inherit = "hr.department"
    _rec_name = "name" # ubah dari display_name to name

    loc = fields.Char('Location')
    is_sales_marketing = fields.Boolean('Is Sales & Marketing dept.')
    is_bod = fields.Boolean('Is Director dept.')
    
    code = fields.Char(string="Code")
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The Code must be unique, this one is already assigned to another Department."),
    ]

    @api.constrains('is_bod','write_date')
    def _constrains_is_bod(self):
        for record in self:
            if record.is_bod:
                dept = self.env['hr.department'].search([
                    ('id','!=',record.id),
                    ('is_bod','=',True)
                ])
                if dept:
                    raise ValidationError(f"Director Department hanya boleh terdiri dari 1 department! \n\ndetail: {dept[0].name}")