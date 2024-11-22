from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date

import ast

class ca_realization_wizard(models.TransientModel):
    _name = 'ca.realization.wizard'
    _description = 'Confirm Wizard'


    product_id = fields.Many2one('product.product', string='Produk', required=True, tracking=True)
    uom_id = fields.Many2one(related="product_id.uom_id")
    desc = fields.Text('Deskripsi', required=True, tracking=True)

    qty = fields.Float('Quantity', required=True, default=1, digits="Product Unit of Measure", tracking=True)
    amount = fields.Monetary(string='Amount', digits='Product Price', required=True, tracking=True)
    total_amount = fields.Monetary(compute='_compute_total_amount', string='Total Amount', digits='Product Price', default=0.0, tracking=True)

    @api.depends('product_id','qty','amount')
    def _compute_total_amount(self):
        for record in self:
            total_amount = 0
            if record.qty and record.amount:
                total_amount = record.qty * record.amount
            record.total_amount = total_amount

    currency_id = fields.Many2one('res.currency', 
        related='company_id.currency_id',
        string='Currency')
    company_id = fields.Many2one("res.company", string="Company", required=True)


    data_id = fields.Integer(string='Data ID')
    model_name = fields.Char(string='Model Name')
    function_name = fields.Char(string='Function Name')
    # string/parameter must be "{a=1,b=2,c=3}"
    function_parameter = fields.Char(string='Function Parameter')



    def btn_continue(self):
        if self.function_name:
            # self.env[self.model_name].search([('id','=',self.data_id)]).with_context(okey=True).eval(self.function_name+self.function_parameter)
            result = getattr(self.env[self.model_name].search([('id','=',self.data_id)]).with_context(
                okey=True, 
                real_desc = self.desc,
                real_qty = self.qty,
                real_amount = self.amount,
                real_total_amount = self.total_amount,
            ), self.function_name)
            if not self.function_parameter:
                return result()
            else:
                # string/parameter = "{a=1,b=2,c=3}"
                args = ast.literal_eval(self.function_parameter)
                return result(**args)
        else:
            pass