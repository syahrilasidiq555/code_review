from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

from datetime import datetime, timedelta,date

class ProductProduct(models.Model):
    _inherit = 'product.product'


    # occupied_ids = fields.One2many('sale.rental.schedule', 'product_id', domain=[('rental_status', '=', 'return')])
    occupied_ids = fields.One2many('sale.rental.schedule', 'product_id', domain=[('report_line_status', '=', 'pickedup')])
    
    rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('occupied', 'Occupied'),
    ], string='Status Rental', compute='_compute_status_rental')
    pickup_date = fields.Datetime('Pickup Date', compute='_compute_status_rental')
    return_date = fields.Datetime('Return Date', compute='_compute_status_rental')
    order_id = fields.Many2one('sale.order', string='Sale Order', compute='_compute_status_rental')
    partner_id = fields.Many2one(related="order_id.partner_id")
    qty_in_rent = fields.Float(digits='Product Unit of Measure')

    uneditable_price_so = fields.Boolean(string='Sale order amount tidak dapat diedit', default=True)

    @api.depends('qty_available','occupied_ids','product_tmpl_id', 'product_tmpl_id.categ_id')
    def _compute_status_rental(self):
        for record in self:
            categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            record.rental_status = 'free' if record.product_tmpl_id.rent_ok and record.qty_available >= 1 else 'not_available'
            record.pickup_date = False
            record.return_date = False
            record.order_id = False

            if record.occupied_ids and record.product_tmpl_id.categ_id.id == categ_columbarium.id:
                for sch in record.occupied_ids:
                    record.rental_status = 'occupied'
                    record.pickup_date = sch.pickup_date
                    record.return_date = sch.return_date
                    record.order_id = sch.order_id
                    break
    
    def name_get(self):
        res_names = super(ProductProduct, self).name_get()
        if not self._context.get('columbarium_search'):
            return res_names
        elif self.env.context.get('columbarium_search', False):
            result = []
            for record in self:
                variant = ""
                for x in record.product_template_variant_value_ids:
                    variant += x.name + ',' 
                name = "{name} ({variant}) - {rental_status}".format(
                    name = record.name, 
                    rental_status = dict(self._fields['rental_status'].selection).get(record.rental_status),
                    variant = variant[:-1]
                )
                if record.rental_status == 'occupied' and record.partner_id:
                    name += " oleh %s " % (str(record.partner_id.name))
                result.append((record.id, name))
            return result



    def action_view_rentals(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            "sale_renting.action_rental_order_schedule")
        action['domain'] = [('product_id', 'in', self.ids)]
        action['context'] = {'create': False, 'search_default_Rentals':1, 'group_by_no_leaf':1, 'search_default_pickedup':1}
        return action
    
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        res = super(ProductProduct, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        return super(ProductProduct, self).write(vals)