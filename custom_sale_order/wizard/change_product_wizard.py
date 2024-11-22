from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import math
import calendar

class ChangeProductWizard(models.TransientModel):
    _name = 'change.product.wizard'
    _description = 'Change Product'

    so_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    currency_id = fields.Many2one(related="so_id.currency_id")
    company_id = fields.Many2one(related='so_id.company_id', string='Company', readonly=True)
    so_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    is_rental = fields.Boolean(related="so_line_id.is_rental")
    pickup_date = fields.Datetime(related="so_line_id.pickup_date")
    return_date = fields.Datetime(related="so_line_id.return_date")

    current_product_id = fields.Many2one(related="so_line_id.product_id", string='Produk')
    current_categ_id = fields.Many2one(related="so_line_id.product_id.categ_id", string='Category')
    current_product_uom_qty = fields.Float(related="so_line_id.product_uom_qty")
    current_price_unit = fields.Float(string='Subtotal', compute="_compute_current_price_unit")
    
    @api.depends('so_line_id','so_line_id.product_id')
    def _compute_current_price_unit(self):
        for record in self:
            record.current_price_unit = 0
            if record.so_line_id.parent_id:
                packet_line = record.so_line_id.parent_id.product_id.product_tmpl_id.ni_bundle_product_ids.filtered(lambda x : x.name.id == record.so_line_id.product_id.product_tmpl_id.id)
                if packet_line:
                    record.current_price_unit = packet_line.price
            
            record.qty = record.current_product_uom_qty

            if self.env.context.get('upgrade_columbarium'):
                record.current_price_unit = record.so_line_id.price_subtotal


    product_id = fields.Many2one('product.product', string='Product', required=True, domain="['&','&',('id','!=',current_product_id),('categ_id','=',current_categ_id),'|',('sale_ok','!=',is_rental),('rent_ok','=',is_rental)]")
    # list_price = fields.Float(related="product_id.list_price", string="Price Unit")
    list_price = fields.Float(compute='_compute_list_price', string='Harga Satuan')
    
    @api.depends('product_id','return_date_new','pickup_date_new')
    def _compute_list_price(self):
        for record in self:
            columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
            record.list_price = 0
            if record.product_id:
                if record.is_rental:
                    record.list_price = 0
                    if record.product_id and record.pickup_date_new and record.return_date_new:
                        record.list_price = record.product_id.product_tmpl_id.get_rental_list_price(
                            product_id = record.product_id,
                            start_date = record.pickup_date_new,
                            end_date = record.return_date_new + timedelta(days=1) if record.product_id.product_tmpl_id.categ_id.id == columbarium_category_id.id else record.return_date_new,
                    )
                else:
                    record.list_price = record.product_id.list_price

            if record.product_id and self.env.context.get('upgrade_columbarium'):
                list_price_based_on_last_product = record.product_id.product_tmpl_id.get_rental_list_price(
                    product_id = record.product_id,
                    start_date = record.pickup_date,
                    end_date = record.return_date + timedelta(days=1),
                )
                # get diff date
                total_days = (record.return_date - record.pickup_date).days + 1
                diff_days = (record.return_date_new - record.pickup_date_new).days + 1
                record.list_price = (list_price_based_on_last_product / total_days) * diff_days

    qty = fields.Integer('Quantity', required=True, default=1)
    subtotal_new = fields.Float(compute='_compute_subtotal_new', string='Subtotal')
    
    @api.depends('list_price','qty')
    def _compute_subtotal_new(self):
        for record in self:
            record.subtotal_new = record.list_price * record.qty

    amount_difference = fields.Float(string='Selisih', compute='_compute_amount_difference')
    pickup_date_new = fields.Datetime(string="Tanggal Pickup")
    return_date_new = fields.Datetime(string="Tanggal Return")


    @api.depends('list_price','qty','so_line_id','current_product_uom_qty','current_price_unit')
    def _compute_amount_difference(self):
        for record in self:
            difference = 0
            difference = (record.list_price * record.qty) - record.current_price_unit
            record.amount_difference = difference
            
            if self.env.context.get('upgrade_columbarium'):
                amount_difference = (record.list_price * record.qty) - record.columbarium_revenue_residual
                record.amount_difference = amount_difference if amount_difference >= 0 else 0


    ##############################
    # Custom for columbarium
    ##############################
    columbarium_day_used = fields.Integer(compute="_compute_day_used_revenue_columbarium", string='Total hari berjalan')
    columbarium_revenue_used = fields.Float(compute="_compute_day_used_revenue_columbarium", string='Total Amount Diakui')
    columbarium_revenue_residual = fields.Float(compute="_compute_day_used_revenue_columbarium", string='Total Amount Sisa')
    

    @api.depends('so_id','so_line_id.order_id','current_categ_id','product_id','current_price_unit','pickup_date','pickup_date_new')
    def _compute_day_used_revenue_columbarium(self):
        for record in self:
            columbarium_day_used = 0
            columbarium_revenue_used = 0
            columbarium_revenue_residual = 0
            columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
            if record.current_categ_id.id == columbarium_category_id.id:
                # get posted deffered revenue
                asset_id = record.so_line_id.invoice_lines[0].move_id.asset_ids[0] if record.so_line_id.invoice_lines and record.so_line_id.invoice_lines[0].move_id.asset_ids else False
                if asset_id:
                    # posted_depreciation_move_ids = asset_id.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
                    used_depreciation_move_ids = asset_id.depreciation_move_ids.filtered(lambda x: x.date >= record.pickup_date.date() and x.date < record.pickup_date_new.date()).sorted(key=lambda l: l.date)
                    columbarium_day_used = len(used_depreciation_move_ids)
                    columbarium_revenue_used = sum(x.amount_total for x in used_depreciation_move_ids)
                    columbarium_revenue_residual = sum(x.amount_total for x in (asset_id.depreciation_move_ids - used_depreciation_move_ids))

                    if columbarium_day_used >= 1 and record.pickup_date == record.pickup_date_new:
                        pickup_date_new = record.pickup_date + timedelta(days=columbarium_day_used)
                        record.pickup_date_new = pickup_date_new
                        record.return_date_new = pickup_date_new + relativedelta(days=-1,years=1)

                columbarium_revenue_residual = columbarium_revenue_residual if columbarium_revenue_residual > 0 else record.current_price_unit

            record.columbarium_day_used = columbarium_day_used
            record.columbarium_revenue_used = columbarium_revenue_used
            record.columbarium_revenue_residual = columbarium_revenue_residual
    
    ##############################
    # Custom for columbarium
    ##############################
            
    def backdate_validation(self):
        for record in self:
            if self.env.context.get('upgrade_columbarium'):
                # raise UserError("%s\n\n%s" % (str((record.pickup_date_new + timedelta(hours=7)).date()),str(datetime.now()+timedelta(hours=7))))
                if (record.pickup_date_new + timedelta(hours=7)).date() <= (datetime.now()+timedelta(hours=7)).date():
                    raise UserError("Tanggal mulai upgrade tidak boleh diisi dengan hari yang sudah terlewat, silahkan mulai upgrade setelah tanggal %s" % str((datetime.now()+timedelta(hours=7)).strftime("%d/%m/%Y")))

    def action_choose(self):
        for record in self:
            record.backdate_validation()
            if not record.product_id:
                raise ValidationError("Anda harus memilih produk pengganti terlebih dahulu!")
            

            sale_order_line_obj = self.env['sale.order.line']
            
            values = {
                'order_id': record.so_id.id,
                'product_id': record.product_id.id,
                'name': '{product_name} (Pengganti Produk {product_old})'.format(
                    product_name = record.product_id.name,
                    product_old = record.so_line_id.product_id.name
                ),
                'product_uom_qty': record.qty,
                'price_unit': record.amount_difference / record.qty if record.amount_difference > 0 else 0,
                'tax_id': [tax.id for tax in record.product_id.product_tmpl_id.taxes_id],
                # 'parent_id': parent.id,
                # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'product_warehouse_id':record.product_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_id.product_tmpl_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                'is_produk_pengganti':True,
            }
            if record.is_rental:
                values['name'] = 'RENTAL - {product_name} (Pengganti Produk {product_old})\n{pickup_date} to {return_date}'.format(
                    product_name = record.product_id.display_name,
                    product_old = record.so_line_id.product_id.name,
                    pickup_date = (record.pickup_date_new+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (record.return_date_new+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                )
                values['is_rental'] = True
                values['reservation_begin'] = record.pickup_date_new
                values['pickup_date'] = record.pickup_date_new
                values['return_date'] = record.return_date_new
            
            # raise UserError(str(values))
            
            if self.env.context.get('upgrade_columbarium'):
                if values.get('is_produk_pengganti'):
                    values.pop('is_produk_pengganti')
                values['name'] = 'RENTAL - {product_name} (Upgrade produk {product_old})\n{pickup_date} to {return_date}'.format(
                    product_name = record.product_id.display_name,
                    product_old = record.so_line_id.product_id.display_name,
                    pickup_date = (record.pickup_date_new+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    return_date = (record.return_date_new+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                )
                values['columbarium_upgrade_parent_id'] = record.so_line_id.id
                columbarium_upgrade = sale_order_line_obj.create(values)
                record.so_line_id.is_columbarium_upgraded = True
            else:
                line_pengganti = sale_order_line_obj.create(values)
                record.so_line_id.product_uom_qty = 0
                record.so_line_id.pengganti_id = line_pengganti.id
                record.so_id._constrains_order_line()
                if record.so_line_id.cost_sheet_line_id:
                    # record.so_line_id.cost_sheet_line_id.product_id.product_tmpl_id.roll_vendor_rollback(record.so_line_id.cost_sheet_line_id.vendor_id.id)
                    # ini kadang masih salah vendor rollbacknya
                    vendor_id = record.so_line_id.cost_sheet_line_id.vendor_id
                    record.so_line_id.cost_sheet_line_id.vendor_id = None
                    record.so_line_id.cost_sheet_line_id._onchange_vendor_id(vendor_id)

                # CASE KALAU YANG DIAKUI DI COLUMBARIUM ITU KESELURUHAN HARGA COLUMBARIUM
                # kalau produk yang diganti columbarium kurangi harga paket dengan harga columbarium dalam child paket tsb dan jumlahkan yang dikurangi tadi ke produk penggani
                # columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
                # if record.so_line_id.parent_id and record.so_line_id.product_id.product_tmpl_id.categ_id.id == columbarium_category_id.id:
                #     record.so_line_id.parent_id.price_unit -= record.current_price_unit
                #     line_pengganti.price_unit += record.current_price_unit