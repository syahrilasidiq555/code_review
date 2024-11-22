# from attr import field
from odoo import models, fields, api, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
# from odoo.tools import email_split, float_is_zero

# from datetime import datetime,timedelta,date
# from dateutil.relativedelta import relativedelta

class irSequence(models.Model):
    _inherit = "ir.sequence"

    # {PREFIX}/052023/001
    # AKAN CREATE PREFIX OTOMATIS JIKA TIDAK ADA
    def get_sequence(self, model, first_prefix, padding=3, context=None):
        sequence = self.sudo().search([('name','=',first_prefix),('padding','=',padding)])
        if not sequence:
            # prefix = first_prefix + '/%(month)s%(y)s/'
            prefix = first_prefix + '/'
            sequence = self.sudo().create({
                'code': model,
                'name': first_prefix,
                'implementation': 'no_gap',
                'prefix': prefix,
                'padding': padding
            })
            
        return self.get_id(sequence.id)