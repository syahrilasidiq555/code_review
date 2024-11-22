from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

from datetime import datetime

class ir_sequence(models.Model):
    _inherit = 'ir.sequence'

  
    def get_sequence_fpk(self, model, last_suffix, padding=5, context=None):
        start_day_of_current_year = datetime.now().date().replace(month=1, day=1)    
        end_day_of_current_year = datetime.now().date().replace(month=12, day=31)
        ids = self.search([('name','=',last_suffix),('padding','=',padding)])
        if not ids:
            suffix = last_suffix + '/%(year)s/%(month)s'
            ids = self.create({
                'name': last_suffix,
                'code': model,
                'implementation': 'no_gap',
                'suffix': suffix,
                'padding': padding,
                'use_date_range':True,
                'date_range_ids':[(0,0,{
                    'date_from':start_day_of_current_year,
                    'date_to':end_day_of_current_year,
                    # 'number_next':1,
                })]
            })
            
        return self.get_id(ids.id)
    