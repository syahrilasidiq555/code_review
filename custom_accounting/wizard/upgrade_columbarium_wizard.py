from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta 


class upgradeColumbariumWizard(models.TransientModel):
    _name = 'upgrade.columbarium.wizard'
    
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    sale_order_line_id = fields.Many2one('sale.order.line')
    currency_id = fields.Many2one(related="sale_order_id.currency_id")
    
    def _get_product_columbarium_id_domain(self):
        columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
        return [('categ_id','=',columbarium_category_id.id)]
    
    product_columbarium_id = fields.Many2one('product.product', string='Columbarium', readonly=True)
    product_upgrade_columbarium_id = fields.Many2one('product.product', string='Columbarium',domain=_get_product_columbarium_id_domain)
    pickup_date = fields.Datetime(string="Tanggal Pickup", default=datetime.now() + timedelta(hours=2), required=True)
    return_date = fields.Datetime(string="Tanggal Return", default=datetime.now() + timedelta(hours=2, days=-1) + relativedelta(years=1), required=True)
    list_price_original = fields.Float(string="Subtotal", readonly=True)
    list_price = fields.Float(compute='_compute_list_price', string='Subtotal')

    price_terpakai = fields.Float(string="Terpakai", compute='_compute_list_price')
    price_sisa = fields.Float(string="Sisa", compute='_compute_list_price')
    price_total = fields.Float(string="Total", compute="_compute_list_price")
    price_perlu_dibayar = fields.Float(string="Total Harus Dibayar", compute="_compute_list_price")
    
    @api.depends('product_upgrade_columbarium_id','return_date','pickup_date')
    def _compute_list_price(self):
        for record in self:
            record.list_price = 0
            if record.product_upgrade_columbarium_id and record.pickup_date and record.return_date:
                record.list_price = record.product_upgrade_columbarium_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.product_upgrade_columbarium_id,
                    start_date = record.pickup_date,
                    end_date = record.return_date + timedelta(days=1),
                )

            dtInvTerpakai = self.env['account.move'].sudo().search([
                ('so_id','=',record.sale_order_id.id),
                ('date','<=',record.pickup_date),
                ('move_type','=','out_invoice'),
                ('state','=','posted')])
            if dtInvTerpakai:
                record.price_terpakai = sum(dtInvTerpakai.mapped('amount_total_in_currency_signed'))
            else:
                record.price_terpakai = 0

            record.price_sisa = record.list_price_original - record.price_terpakai
            record.price_total = record.list_price #- record.price_terpakai
            record.price_perlu_dibayar = record.price_total - record.price_sisa

    def action_upgrade(self):
        for record in self:
            err_msg = ""
            if record.product_upgrade_columbarium_id.rental_status == 'occupied':
                err_msg = "Ruang Columbarium tersebut telah disewa!"
                if record.product_upgrade_columbarium_id.partner_id:
                    err_msg = err_msg[:-1]
                    err_msg += " oleh {} !".format(record.product_upgrade_columbarium_id.partner_id.name)
            elif record.product_upgrade_columbarium_id.rental_status == 'not_available':
                err_msg = "Ruang Columbarium tidak tersedia!"

            if err_msg:
                raise ValidationError(err_msg)
            
            # invoice yg harus di hapus
            dtInvHapus = self.env['account.move'].sudo().search([
                ('so_id','=',record.sale_order_id.id),
                ('date','>',record.pickup_date),
                ('move_type','=','out_invoice'),
                ('state','=','draft')])
            dtInvHapus.sudo().unlink()

            # entry journal yg hapus di hapus juga gaess
            dtEntryHapus = self.env['account.move'].sudo().search([
                ('sale_columnbarium_id','=',record.sale_order_id.id),
                ('date','>',record.pickup_date),
                ('move_type','=','entry'),
                ('state','=','draft')])
            dtEntryHapus.sudo().unlink()
                        
            detail_so = []
            values = {
                'is_rental': True,
                'product_id': record.product_upgrade_columbarium_id.id,
                'name': 'RENTAL - {product_name}\n{pickup_date} to {return_date}'.format(
                    product_name = record.product_upgrade_columbarium_id.name,
                    pickup_date = (record.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (record.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                ),
                'product_uom_qty': 1,
                'price_unit': record.price_perlu_dibayar,
                'tax_id': None,
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) \
                #     if not record.product_upgrade_columbarium_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'] \
                #         .sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_upgrade_columbarium_id.product_tmpl_id.default_stock_warehouse_id.id \
                    if not record.product_upgrade_columbarium_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'] \
                        .sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'reservation_begin': record.pickup_date,
                'pickup_date': record.pickup_date,
                'return_date': record.return_date,
            }
            detail_so.append([0, 0, values])

            so_vals = {
                'partner_id': record.sale_order_id.partner_id.id,
                'penanggungjawab_id': record.sale_order_id.penanggungjawab_id.id,
                'order_line': detail_so
            }
            so_res = self.env['sale.order'].sudo().create(so_vals)
            if so_res:
                record.sale_order_line_id.sudo().write({
                    'sale_columnbarium_upgrade_id': so_res.id,
                    'qty_returned': 1,
                    'return_date':record.pickup_date,
                    # 'name': 'RENTAL - {product_name}\n{pickup_date} to {return_date}'.format(
                    #     product_name = record.product_columbarium_id.name,
                    #     pickup_date = (record.sale_order_line_id.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    #     return_date = (record.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"))
                })
                so_res.sudo().write({
                    'is_rental_order':True,
                    'rental_status':'draft',
                })
                so_res.sudo().action_confirm()