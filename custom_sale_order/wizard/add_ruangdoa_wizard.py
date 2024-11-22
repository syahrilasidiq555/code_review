from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date
# from dateutil.relativedelta import relativedelta 
import json


class addruangdoaWizard(models.TransientModel):
    _name = 'add.ruangdoa.wizard'
    

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")
    

    def _get_product_ruangdoa_id_domain(self):
        ruangdoa_category_id = self.env.ref('custom_sale_order.categ_ruangdoa')
        ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
        return [('categ_id','in',[ruangdoa_category_id.id, ruang_semayam_category_id.id])]
    
    product_ruangdoa_id = fields.Many2one('product.product', string='Ruang Doa',domain=_get_product_ruangdoa_id_domain, required=True)
    tanggal_rental = fields.Date(string='Tanggal', default=datetime.now().date(), required=True)    
    
    jadwal_ruangdoa_id_domain = fields.Char(compute='_compute_jadwal_ruangdoa_id_domain', string='Jadwal Domain')
    @api.depends('sale_order_id','product_ruangdoa_id','tanggal_rental')
    def _compute_jadwal_ruangdoa_id_domain(self):
        for record in self:
            domain = []
            if record.tanggal_rental:
                domain = [
                    ('dayofweek','=',str(record.tanggal_rental.weekday()))
                ]
            record.jadwal_ruangdoa_id_domain = json.dumps(domain)
    jadwal_ruangdoa_id = fields.Many2one('jadwal.ruangdoa', string='Jadwal', required=True)


    @api.onchange('tanggal_rental')
    def _onchange_tanggal_rental(self):
        for record in self:
            if record.jadwal_ruangdoa_id and record.tanggal_rental and record.jadwal_ruangdoa_id.dayofweek != str(record.tanggal_rental.weekday()):
                record.jadwal_ruangdoa_id = False

    list_price = fields.Float(compute='_compute_list_price', string='Subtotal')
    # rental_status_json = fields.Char(compute='_compute_list_price', string='Status Rental')
    rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_list_price', string='Status Rental')
    rental_status_detail = fields.Char(compute='_compute_list_price', string='Status Rental')
    

    @api.depends('product_ruangdoa_id','tanggal_rental','jadwal_ruangdoa_id')
    def _compute_list_price(self):
        for record in self:
            record.list_price = 0
            # record.rental_status_json = None
            record.rental_status = None
            record.rental_status_detail = None
            if record.product_ruangdoa_id and record.tanggal_rental and record.jadwal_ruangdoa_id:
                start_hour = int(record.jadwal_ruangdoa_id.hour_from)
                start_minute = int(round((record.jadwal_ruangdoa_id.hour_from % 1)*60,1))
                start_date = datetime(record.tanggal_rental.year, record.tanggal_rental.month, record.tanggal_rental.day, start_hour, start_minute, 0) - timedelta(hours=7)

                end_hour = int(record.jadwal_ruangdoa_id.hour_to)
                end_minute = int(round((record.jadwal_ruangdoa_id.hour_to % 1)*60,1))
                end_date = datetime(record.tanggal_rental.year, record.tanggal_rental.month, record.tanggal_rental.day, end_hour, end_minute, 0) - timedelta(hours=7)

                record.list_price = record.product_ruangdoa_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.product_ruangdoa_id,
                    start_date = start_date,
                    end_date = end_date,
                )

                rental_status_json = record.product_ruangdoa_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.product_ruangdoa_id,
                    start_date = start_date,
                    end_date = end_date,
                )
                # record.rental_status_json = str(rental_status_json)
                record.rental_status = rental_status_json.get('status')
                record.rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )

    def action_add(self):
        for record in self:
            ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            err_msg = ""
            if record.rental_status in ['not_available','reserve','occupied']:
                err_msg = "Ruang Doa tidak tersedia!"

            if err_msg:
                raise ValidationError(err_msg)

            record.sale_order_id.is_rental_order = True if not record.sale_order_id.is_rental_order else record.sale_order_id.is_rental_order
            record.sale_order_id.rental_status = 'draft' if not record.sale_order_id.rental_status else record.sale_order_id.rental_status
            
            start_hour = int(record.jadwal_ruangdoa_id.hour_from)
            start_minute = int(round((record.jadwal_ruangdoa_id.hour_from % 1)*60,1))
            start_date = datetime(record.tanggal_rental.year, record.tanggal_rental.month, record.tanggal_rental.day, start_hour, start_minute, 0) - timedelta(hours=7)

            end_hour = int(record.jadwal_ruangdoa_id.hour_to)
            end_minute = int(round((record.jadwal_ruangdoa_id.hour_to % 1)*60,1))
            end_date = datetime(record.tanggal_rental.year, record.tanggal_rental.month, record.tanggal_rental.day, end_hour, end_minute, 0) - timedelta(hours=7)
            
            values = {
                'is_rental': True,
                'product_id': record.product_ruangdoa_id.id,
                'name': 'RENTAL {ruang_doa} - {product_name}\n{pickup_date} to {return_date}'.format(
                    ruang_doa = 'RUANG DOA' if record.product_ruangdoa_id.categ_id.id == ruang_semayam_category_id.id else '',
                    product_name = record.product_ruangdoa_id.name,
                    pickup_date = (start_date + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (end_date + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                ),
                'product_uom_qty': 1,
                'price_unit': record.list_price,
                'tax_id': None,
                'tax_id': [tax.id for tax in record.product_ruangdoa_id.product_tmpl_id.taxes_id],
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_ruangdoa_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_ruangdoa_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_ruangdoa_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'reservation_begin': start_date,
                'pickup_date': start_date,
                'return_date': end_date,
            }
            record.sale_order_id.order_line = [(0,0,values)]