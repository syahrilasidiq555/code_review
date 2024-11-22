from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta 


class addColumbariumWizard(models.TransientModel):
    _name = 'add.columbarium.wizard'
    

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")
    

    def _get_product_columbarium_id_domain(self):
        columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
        return [('categ_id','=',columbarium_category_id.id)]
    
    product_columbarium_id = fields.Many2one('product.product', string='Columbarium',domain=_get_product_columbarium_id_domain)
    pickup_date = fields.Datetime(string="Tanggal Pickup", default=datetime.now() + timedelta(hours=2), required=True)
    return_date = fields.Datetime(string="Tanggal Return", default=datetime.now() + timedelta(hours=2, days=-1) + relativedelta(years=1), required=True)
    list_price = fields.Float(compute='_compute_list_price', string='Subtotal')
    
    @api.depends('product_columbarium_id','return_date','pickup_date')
    def _compute_list_price(self):
        for record in self:
            record.list_price = 0
            if record.product_columbarium_id and record.pickup_date and record.return_date:
                record.list_price = record.product_columbarium_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.product_columbarium_id,
                    start_date = record.pickup_date,
                    end_date = record.return_date + timedelta(days=1),
                )


    def action_add(self):
        for record in self:
            err_msg = ""
            if record.product_columbarium_id.rental_status == 'occupied':
                err_msg = "Ruang Columbarium tersebut telah disewa!"
                if record.product_columbarium_id.partner_id:
                    err_msg = err_msg[:-1]
                    err_msg += " oleh {} !".format(record.product_columbarium_id.partner_id.name)
            elif record.product_columbarium_id.rental_status == 'not_available':
                err_msg = "Ruang Columbarium tidak tersedia!"

            if err_msg:
                raise ValidationError(err_msg)

            record.sale_order_id.is_rental_order = True if not record.sale_order_id.is_rental_order else record.sale_order_id.is_rental_order
            record.sale_order_id.rental_status = 'draft' if not record.sale_order_id.rental_status else record.sale_order_id.rental_status
            
            values = {
                'is_rental': True,
                'product_id': record.product_columbarium_id.id,
                'name': 'RENTAL - {product_name}\n{pickup_date} to {return_date}'.format(
                    product_name = record.product_columbarium_id.display_name,
                    pickup_date = (record.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (record.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                ),
                'product_uom_qty': 1,
                'price_unit': record.list_price,
                # 'tax_id': None,
                'tax_id': [tax.id for tax in record.product_columbarium_id.product_tmpl_id.taxes_id],
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_columbarium_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_columbarium_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_columbarium_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'reservation_begin': record.pickup_date,
                'pickup_date': record.pickup_date,
                'return_date': record.return_date,
            }
            record.sale_order_id.order_line = [(0,0,values)]