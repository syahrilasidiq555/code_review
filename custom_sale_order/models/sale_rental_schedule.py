from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

from datetime import datetime, timedelta,date

class SaleRentalSchedule(models.Model):
    _inherit = 'sale.rental.schedule'


    def action_view_so(self):
        for record in self:
            if record.order_id:
                form_view_id = self.env.ref("sale.view_order_form").id
                name = 'Sale Order'
                if record.order_id.is_rental_order:
                    form_view_id = self.env.ref("sale_renting.rental_order_primary_form_view").id
                    name = 'Rental Order'
        
                result = {
                    'name': _(name),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    # 'view_type': 'form',
                    'views': [(form_view_id, 'form')],
                    'res_id': self.order_id.id,
                    'context': {'create': False},
                }
                return result  
            else:
                raise UserError("Sales Order not available")