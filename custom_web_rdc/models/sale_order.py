from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_form_id = fields.Many2one('customer.form.website', string='Customer Form')


    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        
        # add customer form to sale_order
        if res.customer_form_id:
            res.customer_form_id.sale_order_id = res.id

        return res