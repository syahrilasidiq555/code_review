from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date

class addTransportasiWizard(models.TransientModel):
    _name = 'add.transportasi.wizard'
    _description = 'Add Transportasi Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    currency_id = fields.Many2one(related="sale_order_id.currency_id")

    def _get_product_transportasi_id_domain(self):
        categ_transport_id = self.env.ref('custom_sale_order.categ_transportasi_jenazah')
        # return [('categ_id','=', categ_transport_id.id),('qty_available','>=',1)]
        return [('categ_id','=', categ_transport_id.id)]

    product_transportasi_id = fields.Many2one('product.product', string='Transportasi', domain=_get_product_transportasi_id_domain, required=True)
    tarif_id = fields.Many2one('master.tarif.ambulance', string='Tujuan', required=True)
    pickup_date = fields.Datetime(string="Tanggal Pickup", default=datetime.now() + timedelta(hours=2), required=True)
    return_date = fields.Datetime(string="Tanggal Return", default=datetime.now() + timedelta(days=1), required=True)

    # rental_status_json = fields.Char(compute='_compute_list_price', string='Status Rental')
    rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_list_price', string='Status Rental')
    rental_status_detail = fields.Char(compute='_compute_list_price', string='Status Rental')

    @api.depends('product_transportasi_id','pickup_date','return_date')
    def _compute_list_price(self):
        for record in self:
            # record.rental_status_json = None
            record.rental_status = None
            record.rental_status_detail = None
            if record.product_transportasi_id and record.pickup_date and record.return_date:
                rental_status_json = record.product_transportasi_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.product_transportasi_id,
                    start_date = record.pickup_date,
                    end_date = record.return_date,
                )
                # record.rental_status_json = str(rental_status_json)
                record.rental_status = rental_status_json.get('status')
                record.rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )


    def action_add(self):
        for record in self:
            err_msg = ""
            if record.rental_status in ['not_available','reserve','occupied']:
                err_msg = "Transportasi tidak tersedia!"

            if err_msg:
                raise ValidationError(err_msg)
            
            record.sale_order_id.is_rental_order = True if not record.sale_order_id.is_rental_order else record.sale_order_id.is_rental_order
            record.sale_order_id.rental_status = 'draft' if not record.sale_order_id.rental_status else record.sale_order_id.rental_status
            
            values = {
                'is_from_transportasi_wizard':True,
                'is_rental': True,
                'product_id': record.product_transportasi_id.id,
                'name': 'RENTAL - {product_name} ({tujuan})\n{pickup_date} to {return_date}'.format(
                    product_name = record.product_transportasi_id.name,
                    tujuan = record.tarif_id.kota,
                    pickup_date = (record.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (record.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                ),
                'product_uom_qty': 1,
                'price_unit': record.tarif_id.tarif,
                'tax_id': None,
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_transportasi_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_transportasi_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_transportasi_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'reservation_begin': record.pickup_date,
                'pickup_date': record.pickup_date,
                'return_date': record.return_date,
            }
            record.sale_order_id.order_line = [(0,0,values)]

            if self.env.context.get('active_model') == 'customer.form.website':
                # raise UserError(str(self.env.context))
                customer_form = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
                customer_form.jenazah_id.transportasi_id = record.product_transportasi_id
                if customer_form.almarhum_transportasi_sale_order_line_id:
                    customer_form.almarhum_transportasi_sale_order_line_id.unlink()
                customer_form.almarhum_transportasi_sale_order_line_id = record.sale_order_id.order_line[-1].id
                