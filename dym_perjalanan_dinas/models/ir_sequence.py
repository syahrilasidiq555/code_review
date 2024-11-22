# from attr import field
from odoo import models, fields, api, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
# from odoo.tools import email_split, float_is_zero

from datetime import datetime,timedelta,date
# from dateutil.relativedelta import relativedelta

class irSequence(models.Model):
    _inherit = "ir.sequence"

    # {PREFIX}/052023/001
    # AKAN CREATE PREFIX OTOMATIS JIKA TIDAK ADA
    def get_sequence_pd(self, model, first_prefix, suffix, padding=3, context=None):
        start_day_of_current_year = datetime.now().date().replace(month=1, day=1)    
        end_day_of_current_year = datetime.now().date().replace(month=12, day=31)

        sequence = self.sudo().search([('name','=',first_prefix), ('padding','=',padding)])
        if not sequence:
            prefix = first_prefix + '/%(month)s%(y)s/'
            sequence = self.sudo().create({
                'code': model,
                'name': first_prefix,
                'implementation': 'no_gap',
                'prefix': prefix,
                'suffix': suffix,
                'padding': padding,
                'use_date_range':True,
                'date_range_ids':[(0,0,{
                    'date_from':start_day_of_current_year,
                    'date_to':end_day_of_current_year,
                    # 'number_next':1,
                })]
            })
            
        return self.get_id(sequence.id)