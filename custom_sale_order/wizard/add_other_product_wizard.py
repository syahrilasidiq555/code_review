from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date


class addOtherProductWizard(models.TransientModel):
    _name = 'add.other.product.wizard'
    
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")


    product_id = fields.Many2one('product.product', string='Product')


    def action_add(self):
        for record in self:
            raise UserError("add prodct!")