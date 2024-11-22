from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date

class addLarungWizard(models.TransientModel):
    _name = 'add.larung.wizard'
    _description = 'Add Larung Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")

    def _get_default_product_id(self):
        try:
            product_larung_id = self.env.ref('custom_sale_order.product_larung')
            if product_larung_id:
                default = product_larung_id.id
        except:
            default = False

        return default

    product_id = fields.Many2one('product.product', string='Product', required=True, default=_get_default_product_id)
    name = fields.Char(string='Deskripsi', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True, domain=[('is_vendor','=',True)])
    list_price = fields.Float(string='Subtotal')

    @api.onchange('product_id','vendor_id')
    def _onchange_product_id(self):
        for record in self:
            list_price = 0
            # name = "" if not record.name else record.name
            if record.product_id:
                # name = record.product_id.display_name
                list_price = record.product_id.list_price
                if record.vendor_id:
                    for x in record.product_id.seller_ids.filtered(lambda x: x.name.id == record.vendor_id.id):
                        list_price = x.price
                        break

            record.list_price = list_price
            # record.name = name

    def action_add(self):
        for record in self:
            # err_msg = ""
            # if record.rental_status in ['not_available','reserve','occupied']:
            #     err_msg = "Transportasi tidak tersedia!"

            # if err_msg:
            #     raise ValidationError(err_msg)
            
            # record.sale_order_id.is_rental_order = True if not record.sale_order_id.is_rental_order else record.sale_order_id.is_rental_order
            # record.sale_order_id.rental_status = 'draft' if not record.sale_order_id.rental_status else record.sale_order_id.rental_status
            
            values = {
                # 'is_rental': True,
                'default_vendor_id': record.vendor_id.id,
                'product_id': record.product_id.id,
                'name': record.name,
                'product_uom_qty': 1,
                'price_unit': record.list_price,
                # 'tax_id': None,
                'tax_id': [tax.id for tax in record.product_id.product_tmpl_id.taxes_id],
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
            }
            record.sale_order_id.order_line = [(0,0,values)]

            if self.env.context.get('active_model') == 'customer.form.website':
                # raise UserError(str(self.env.context))
                customer_form = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
                customer_form.jenazah_id.larung_vendor_id = record.vendor_id
                if customer_form.almarhum_larung_sale_order_line_id:
                    customer_form.almarhum_larung_sale_order_line_id.unlink()
                customer_form.almarhum_larung_sale_order_line_id = record.sale_order_id.order_line[-1].id
                