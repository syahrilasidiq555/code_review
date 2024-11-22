from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date
import math
import json

class addRuangSemayamWizard(models.TransientModel):
    _name = 'add.ruang.semayam.wizard'
    _description = 'Add Ruang Semayam Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")
    type = fields.Selection([
        # ('baru', 'Tambah Ruang Semayam Baru'),
        ('tambah_hari', 'Penambahan Hari'),
        ('tambah_lebar', 'Penambahan Lebar'),
        ('tambah_hari_dan_lebar', 'Penambahan Hari dan Lebar'),
    ], string='Tipe', required=True)

    # tambah produk baru
    def _get_ruang_semayam_id_domain(self):
        ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
        return [('categ_id','=',ruang_semayam_category_id.id)]
    
    ruang_semayam_id = fields.Many2one('product.product', string='Ruang Semayam',domain=_get_ruang_semayam_id_domain)
    pickup_date = fields.Datetime(string="Tanggal Pickup", default=datetime.now() + timedelta(hours=2))
    return_date = fields.Datetime(string="Tanggal Return", default=datetime.now().replace(hour=23, minute=59, second=59) - timedelta(hours=7))

    list_price = fields.Float(compute='_compute_list_price', string='Subtotal')
    rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_list_price', string='Status Rental')
    rental_status_detail = fields.Char(compute='_compute_list_price', string='Status Rental')

    @api.depends('ruang_semayam_id','return_date','pickup_date')
    def _compute_list_price(self):
        for record in self:
            record.list_price = 0
            record.rental_status = None
            record.rental_status_detail = None
            if record.ruang_semayam_id and record.pickup_date and record.return_date:
                record.list_price = record.ruang_semayam_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.ruang_semayam_id,
                    start_date = (record.pickup_date + timedelta(hours=7)).date(),
                    end_date = (record.return_date + timedelta(days=1, hours=7)).date(),
                    exclude_hour = True,
                )
            
                record.list_price = record.ruang_semayam_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.ruang_semayam_id,
                    start_date = (record.pickup_date + timedelta(hours=7)).date(),
                    end_date = (record.return_date + timedelta(days=1, hours=7)).date(),
                    exclude_hour = True,
                )

                rental_status_json = record.ruang_semayam_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.ruang_semayam_id,
                    start_date = (record.pickup_date + timedelta(hours=7)).date(),
                    end_date = (record.return_date + timedelta(days=1, hours=7)).date(),
                )
                # record.rental_status_json = str(rental_status_json)
                record.rental_status = rental_status_json.get('status')
                record.rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )

    # tambah hari & lebar
    so_ruang_semayam_id = fields.Many2one(related="sale_order_id.ruang_semayam_id")
    so_ruang_semayam_order_line_id = fields.Many2one(related='sale_order_id.ruang_semayam_order_line_id')

    # tambah hari
    so_pickup_date = fields.Datetime(related="so_ruang_semayam_order_line_id.pickup_date")
    so_return_date = fields.Datetime(related="so_ruang_semayam_order_line_id.return_date")

    pickup_date_new = fields.Datetime(string="Tanggal Pickup", compute='_compute_pickup_date_new')
    @api.depends('so_ruang_semayam_order_line_id','so_ruang_semayam_order_line_id.so_return_date','so_return_date')
    def _compute_pickup_date_new(self):
        for record in self:
            record.pickup_date_new = False
            if record.so_ruang_semayam_order_line_id:
                record.pickup_date_new = record.so_ruang_semayam_order_line_id.return_date.replace(hour=0, minute=0, second=0) + timedelta(days=1, hours=-7)

    return_date_new = fields.Datetime(string="Tanggal Return")
    tambah_hari_list_price = fields.Float(compute='_compute_tambah_hari_list_price', string='Subtotal')
    tambah_hari_rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_tambah_hari_list_price', string='Status Rental')
    tambah_hari_rental_status_detail = fields.Char(compute='_compute_tambah_hari_list_price', string='Status Rental')
    @api.depends('so_ruang_semayam_id','so_return_date','return_date_new','pickup_date_new')
    def _compute_tambah_hari_list_price(self):
        for record in self:
            record.tambah_hari_list_price = 0
            record.tambah_hari_rental_status = None
            record.tambah_hari_rental_status_detail = None
            if record.so_ruang_semayam_id and record.pickup_date_new and record.return_date_new:
                record.tambah_hari_list_price = record.so_ruang_semayam_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.so_ruang_semayam_id,
                    start_date = (record.pickup_date_new + timedelta(hours=7)).date(),
                    end_date = (record.return_date_new + timedelta(days=1, hours=7)).date(),
                    exclude_hour = True,
                )

                rental_status_json = record.so_ruang_semayam_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.so_ruang_semayam_id,
                    start_date = (record.pickup_date_new + timedelta(hours=7)).date(),
                    end_date = (record.return_date_new + timedelta(days=1, hours=7)).date(),
                )
                # record.rental_status_json = str(rental_status_json)
                record.tambah_hari_rental_status = rental_status_json.get('status')
                record.tambah_hari_rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.tambah_hari_rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )

    # tambah lebar
    ruang_semayam_variant_id_domain = fields.Char(compute='_compute_ruang_semayam_variant_id_domain', string='Ruang Semayam Variant Domain')
    @api.depends('sale_order_id','so_ruang_semayam_order_line_id','so_ruang_semayam_id')
    def _compute_ruang_semayam_variant_id_domain(self):
        for record in self:
            domain = []
            if record.so_ruang_semayam_id:
                domain = [('id','!=',record.so_ruang_semayam_id.id),('qty_available','>=',1)]
            if record.so_ruang_semayam_id and record.so_ruang_semayam_order_line_id:
                domain = [
                    ('id','!=',record.so_ruang_semayam_id.id),
                    ('qty_available','>=',1),
                    ('product_tmpl_id','=',record.so_ruang_semayam_id.product_tmpl_id.id),
                ]
            record.ruang_semayam_variant_id_domain = json.dumps(domain)

    ruang_semayam_variant_id = fields.Many2one('product.product', string='Ruang Semayam')

    start_date_new_lebar = fields.Datetime(string="Tanggal Pickup")
    return_date_new_lebar = fields.Datetime(string="Tanggal Return")
    
    tambah_lebar_list_price = fields.Float(compute='_compute_tambah_lebar_list_price', string='Subtotal')
    tambah_lebar_rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_tambah_lebar_list_price', string='Status Rental')
    tambah_lebar_rental_status_detail = fields.Char(compute='_compute_tambah_lebar_list_price', string='Status Rental')
    @api.depends('ruang_semayam_variant_id','start_date_new_lebar','return_date_new_lebar')
    def _compute_tambah_lebar_list_price(self):
        for record in self:
            record.tambah_lebar_list_price = 0
            record.tambah_lebar_rental_status = None
            record.tambah_lebar_rental_status_detail = None
            if record.ruang_semayam_variant_id and record.start_date_new_lebar and record.return_date_new_lebar:
                record.tambah_lebar_list_price = record.ruang_semayam_variant_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.ruang_semayam_variant_id,
                    start_date = (record.start_date_new_lebar + timedelta(hours=7)).date(),
                    end_date = (record.return_date_new_lebar + timedelta(days=1, hours=7)).date(),
                    exclude_hour = True,
                )

                rental_status_json = record.ruang_semayam_variant_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.ruang_semayam_variant_id,
                    start_date = (record.start_date_new_lebar + timedelta(hours=7)).date(),
                    end_date = (record.return_date_new_lebar + timedelta(days=1, hours=7)).date(),
                )
                # record.rental_status_json = str(rental_status_json)
                record.tambah_lebar_rental_status = rental_status_json.get('status')
                record.tambah_lebar_rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.tambah_lebar_rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )

    def add_ruang_semayam(self):
        for record in self:          
            # sepertinya masih ada issue terkait pickup di SO
            record.sale_order_id.is_rental_order = True if not record.sale_order_id.is_rental_order else record.sale_order_id.is_rental_order
            record.sale_order_id.rental_status = 'draft' if not record.sale_order_id.rental_status else record.sale_order_id.rental_status
            
            if record.type == 'baru':
                err_msg = ""
                if record.rental_status in ['not_available','reserve','occupied']:
                    err_msg = "Ruang Semayam tidak tersedia pada jam dan tanggal berikut!"

                if err_msg:
                    raise ValidationError(err_msg)
                
                record.sale_order_id._validasi_tambah_ruang_semayam_baru()
                values = {
                    'is_from_ruang_semayam_wizard':True,
                    'is_rental': True,
                    'product_id': record.ruang_semayam_id.id,
                    'name': 'RENTAL - {product_name}\n{pickup_date} to {return_date}'.format(
                        product_name = record.ruang_semayam_id.name,
                        pickup_date = (record.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                        return_date = (record.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    ),
                    'product_uom_qty': 1,
                    'price_unit': record.list_price,
                    # 'tax_id': None,
                    'tax_id': [tax.id for tax in record.ruang_semayam_id.product_tmpl_id.taxes_id],
                    # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.ruang_semayam_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'product_warehouse_id':record.ruang_semayam_id.product_tmpl_id.default_stock_warehouse_id.id if not record.ruang_semayam_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'reservation_begin': record.pickup_date,
                    'pickup_date': record.pickup_date,
                    'return_date': record.return_date,
                }
                record.sale_order_id.order_line = [(0,0,values)]
            if record.type in ['tambah_hari','tambah_hari_dan_lebar']:
                err_msg = ""
                if record.tambah_hari_rental_status in ['not_available','reserve','occupied']:
                    err_msg = "Ruang Semayam untuk tambah hari tidak tersedia pada jam dan tanggal berikut!"

                if err_msg:
                    raise ValidationError(err_msg)
                
                record.sale_order_id._validasi_tambah_hari_lebar_ruang_semayam()
                values = {
                    'is_from_ruang_semayam_wizard':True,
                    'jenis_tambahan_ruang_semayam':'hari',
                    'is_rental': True,
                    'product_id': record.so_ruang_semayam_id.id,
                    'name': 'RENTAL - {product_name} (Tambah Hari)\n{pickup_date} to {return_date}'.format(
                        product_name = record.so_ruang_semayam_id.name,
                        pickup_date = (record.so_return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                        return_date = (record.return_date_new+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    ),
                    'product_uom_qty': 1,
                    'price_unit': record.tambah_hari_list_price,
                    # 'tax_id': None,
                    'tax_id': [tax.id for tax in record.so_ruang_semayam_id.product_tmpl_id.taxes_id],
                    # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.so_ruang_semayam_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'product_warehouse_id':record.so_ruang_semayam_id.product_tmpl_id.default_stock_warehouse_id.id if not record.so_ruang_semayam_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'reservation_begin': record.so_return_date,
                    'pickup_date': record.so_return_date,
                    'return_date': record.return_date_new,
                }
                record.sale_order_id.order_line = [(0,0,values)]

            if record.type in ['tambah_lebar','tambah_hari_dan_lebar']:
                err_msg = ""
                if record.tambah_lebar_rental_status in ['not_available','reserve','occupied']:
                    err_msg = "Ruang Semayam untuk tambah lebar tidak tersedia pada jam dan tanggal berikut!"

                if err_msg:
                    raise ValidationError(err_msg)
                
                record.sale_order_id._validasi_tambah_hari_lebar_ruang_semayam()
                values = {
                    'is_from_ruang_semayam_wizard':True,
                    'jenis_tambahan_ruang_semayam':'lebar',
                    'is_rental': True,
                    'product_id': record.ruang_semayam_variant_id.id,
                    'name': 'RENTAL - {product_name} (Tambah Lebar)\n{pickup_date} to {return_date}'.format(
                        product_name = record.ruang_semayam_variant_id.name,
                        pickup_date = (record.start_date_new_lebar+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                        return_date = (record.return_date_new_lebar+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    ),
                    'product_uom_qty': 1,
                    'price_unit': record.tambah_lebar_list_price,
                    # 'tax_id': None,
                    'tax_id': [tax.id for tax in record.ruang_semayam_variant_id.product_tmpl_id.taxes_id],
                    # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.ruang_semayam_variant_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'product_warehouse_id':record.ruang_semayam_variant_id.product_tmpl_id.default_stock_warehouse_id.id if not record.ruang_semayam_variant_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'reservation_begin': record.start_date_new_lebar,
                    'pickup_date': record.start_date_new_lebar,
                    'return_date': record.return_date_new_lebar,
                }
                record.sale_order_id.order_line = [(0,0,values)]