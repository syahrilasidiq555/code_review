from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import math

class ProductProduct(models.Model):
    _inherit = 'product.template'

    default_stock_warehouse_id = fields.Many2one('stock.warehouse', string='Lokasi Gudang Default')

    account_penangguhan_id = fields.Many2one('account.account', string='Akun Penangguhan Pendapatan', 
        domain="[('internal_type','=','other'),('deprecated','=',False),('company_id','=',current_company_id),('is_off_balance','=',False)]")

    pendapatan_asset_model_id = fields.Many2one('account.asset',compute='_compute_pendapatan_asset_model_id', string='Penangguhan Pendapatan Model', store=True)
    pendapatan_asset_model_id_method_number = fields.Integer(related="pendapatan_asset_model_id.method_number")
    pendapatan_asset_model_id_method_period = fields.Selection(related="pendapatan_asset_model_id.method_period")
    
    @api.depends('account_penangguhan_id')
    def _compute_pendapatan_asset_model_id(self):
        for record in self:
            categ_columbarium = False
            record.pendapatan_asset_model_id = False
            try:
                categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            except:
                pass
            # record.pendapatan_asset_model_id = False
            if categ_columbarium and record.categ_id.id == categ_columbarium.id:
                if record.account_penangguhan_id and not record.pendapatan_asset_model_id:
                    # create model penangguhan pendapatan
                    vals = {
                        'name': "Penagguhan Pendapatan " + record.name,
                        'asset_type': 'sale',
                        'state': 'model',
                        'account_depreciation_id': categ_columbarium.property_account_income_categ_id.id,
                        'account_depreciation_expense_id': record.account_penangguhan_id.id,
                        'journal_id': self.env.ref('custom_sale_order.journal_pendapatan_columbarium').id,
                        'method_number':365,
                        'method_period':'-1'
                    }
                    # raise ValidationError(str(vals))
                    # pendapatan_asset_model_id = 
                    record.pendapatan_asset_model_id = self.env['account.asset'].create(vals)
                else:
                    if record.pendapatan_asset_model_id:
                        record.pendapatan_asset_model_id.account_depreciation_expense_id = record.account_penangguhan_id
                

    is_konsinyasi = fields.Boolean(string="is Konsinyasi", default=False)
    @api.onchange('detailed_type')
    def _onchange_detailed_type(self):
        for record in self:
            if record.detailed_type != 'product':
                record.is_konsinyasi = False

    vendor_konsinyasi_id = fields.Many2one('res.partner', compute='_compute_vendor_konsinyasi_id', string='Vendor Pemilik Produk')
    @api.depends('is_konsinyasi','seller_ids','seller_ids.name')
    def _compute_vendor_konsinyasi_id(self):
        for record in self:
            vendor_konsinyasi_id = False
            if record.is_konsinyasi and record.seller_ids:
                vendor_konsinyasi_id = record.seller_ids[0].name.id
            record.vendor_konsinyasi_id = vendor_konsinyasi_id

    ni_is_product_pack = fields.Boolean(string="Is Product Pack")
    pelebaran_ruangan = fields.Boolean(string='Pelebaran Ruangan')
    jumlah_voucher_parkir = fields.Integer(string='Jumlah Voucher Parkir')
    ni_cal_pack_price = fields.Boolean(string="Auto Calculate SUM Pack Price")
    ni_bundle_product_ids = fields.One2many('bundle.product', 'ni_product_id', string="Bundle Products")

    # list_price = fields.Float(
    #     'Sales Price', compute='_compute_list_price',
    #     digits=dp.get_precision('Product Price'),
    #     help="Price at which the product is sold to customers.")

    pack_price = fields.Float(compute='_compute_pack_price', string='Sales Price', store=True)
    @api.depends('ni_bundle_product_ids','ni_bundle_product_ids.price','ni_cal_pack_price')
    def _compute_pack_price(self):
        for record in self:
            record.pack_price = record.get_pack_price()
            record.list_price = record.get_pack_price() if record.ni_cal_pack_price else record.list_price


    @api.constrains('is_konsinyasi','attribute_line_ids','attribute_line_ids.attribute_id','attribute_line_ids.value_ids')
    def _constrains_is_konsinyasi(self):
        for record in self:
            if record.is_konsinyasi:
                if record.attribute_line_ids:
                    raise ValidationError("Produk Konsinaysi tidak boleh memiliki varian!")

    @api.onchange('is_konsinyasi','ni_is_product_pack')
    def _onchange_is_konsinyasi(self):
        for record in self:
            if record.is_konsinyasi or record.ni_is_product_pack:
                if record.attribute_line_ids:
                    record.attribute_line_ids = False

    @api.onchange('ni_cal_pack_price')
    def _onchange_ni_cal_pack_price(self):
        for record in self:
            record.list_price = record.get_pack_price()


    def get_pack_price(self):
        for record in self:
            pack_price = 0
            if record.ni_cal_pack_price:
                for bundle_product in record.ni_bundle_product_ids:
                    pack_price += bundle_product.price
            return pack_price

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if vals.get('ni_is_product_pack'):
            if vals.get('attribute_line_ids'):
                raise ValidationError(
                    _('You cannot create the variant of the Product which is Pack!!!'))

        return res

    # @api.model
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if self.ni_is_product_pack:
            if self.attribute_line_ids:
                raise ValidationError(
                    _('You cannot create the variant of the Product which is Pack!!!'))

        return res
    

    # inherit fungsi di odoo enterprise
    def action_view_rentals(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            "sale_renting.action_rental_order_schedule")
        action['domain'] = [('product_id', 'in', self.mapped('product_variant_ids').ids)]
        action['context'] = {'create': False, 'search_default_Rentals':1, 'group_by_no_leaf':1, 'search_default_pickedup':1}
        return action
    
    ###############################################################
    ##   METHOD
    ############################################################### 

    # get list price for rental
    def get_rental_list_price(self,product_id,start_date,end_date, exclude_hour=False):
        for record in self:
            if product_id:
                price = 0
                delta = end_date - start_date

                # syahril 07/01/2024
                diff = relativedelta(end_date,start_date)

                pricings = product_id.rental_pricing_ids.filtered(lambda x: product_id.id in x.product_variant_ids.ids) if product_id.product_tmpl_id.product_variant_count > 1 else product_id.rental_pricing_ids

                pricings_hour = []
                pricings_day = []
                pricings_week = []
                pricings_month = []


                # hour
                if diff.hours and not exclude_hour:
                    for pricing in pricings.filtered(lambda x: x.unit == 'hour'):
                        pricings_hour.append({
                            'price':pricing.price,
                            'duration':pricing.duration,
                        })
                    pricings_hour = sorted(pricings_hour, reverse=True, key=lambda x: x['duration'])
                # day
                if diff.days % 7:
                    for pricing in pricings.filtered(lambda x: x.unit == 'day'):
                        pricings_day.append({
                            'price':pricing.price,
                            'duration':pricing.duration,
                        })
                    pricings_day = sorted(pricings_day, reverse=True, key=lambda x: x['duration'])
                # week
                if ( diff.days - (diff.days%7) ) / 7:
                    for pricing in pricings.filtered(lambda x: x.unit == 'week'):
                        pricings_week.append({
                            'price':pricing.price,
                            'duration':pricing.duration,
                        })
                    pricings_week = sorted(pricings_week, reverse=True, key=lambda x: x['duration'])
                # month
                if diff.months or diff.years:
                    for pricing in pricings.filtered(lambda x: x.unit == 'month'):
                        pricings_month.append({
                            'price':pricing.price,
                            'duration':pricing.duration,
                        })
                    pricings_month = sorted(pricings_month, reverse=True, key=lambda x: x['duration'])
                    
                # loop every pricings
                # month                    
                if pricings_month:
                    diff_month = diff.months
                    diff_month += 12 * diff.years if diff.years else 0
                    while diff_month > 0 :
                        for pricing_month in pricings_month:
                            if diff_month >= pricing_month['duration']:
                                price += pricing_month['price']
                                diff_month -= pricing_month['duration']
                                found = True
                                break
                            else:
                                found = False
                        if diff_month < pricings_month[-1]['duration'] and not found:
                            price += pricings_month[-1]['price']/pricings_month[-1]['duration'] * diff_month
                            diff_month = 0

                # week                    
                if pricings_week:
                    diff_week = ( diff.days - (diff.days%7) ) / 7
                    while diff_week > 0 :
                        for pricing_week in pricings_week:
                            if diff_week >= pricing_week['duration']:
                                price += pricing_week['price']
                                diff_week -= pricing_week['duration']
                                found = True
                                break
                            else:
                                found = False
                        if diff_week < pricings_week[-1]['duration'] and not found:
                            price += pricings_week[-1]['price']/pricings_week[-1]['duration'] * diff_week
                            diff_week = 0

                # day                    
                if pricings_day:
                    diff_day = diff.days % 7
                    while diff_day > 0 :
                        for pricing_day in pricings_day:
                            if diff_day >= pricing_day['duration']:
                                price += pricing_day['price']
                                diff_day -= pricing_day['duration']
                                found = True
                                break
                            else:
                                found = False
                        if diff_day < pricings_day[-1]['duration'] and not found:
                            price += pricings_day[-1]['price']/pricings_day[-1]['duration'] * diff_day
                            diff_day = 0

                # hour                    
                if pricings_hour:
                    diff_hour = diff.hours
                    while diff_hour > 0 :
                        for pricing_hour in pricings_hour:
                            if diff_hour >= pricing_hour['duration']:
                                price += pricing_hour['price']
                                diff_hour -= pricing_hour['duration']
                                found = True
                                break
                            else:
                                found = False
                        if diff_hour < pricings_hour[-1]['duration'] and not found:
                            price += pricings_hour[-1]['price']/pricings_hour[-1]['duration'] * diff_hour
                            diff_hour = 0
                
                
                # code lama
                # for pricing in pricings:
                #     if pricing.unit == 'hour':
                #         price = pricing.price/pricing.duration * (math.floor(delta.seconds / 3600) + math.floor(delta.days)*24)
                #     elif pricing.unit == 'day':
                #         price = pricing.price/pricing.duration * (delta.days)
                #     elif pricing.unit == 'week':
                #         price = pricing.price/pricing.duration * (math.floor(delta.days / 7))
                #     elif pricing.unit == 'month':
                #         price = pricing.price/pricing.duration * (math.floor(delta.days / 30))
                # raise UserError(pricing.price/pricing.duration * (math.floor(delta.seconds / 3600)))
                return price

    # get status rental
    def get_rental_status_info(self,product_id,start_date,end_date):
        for record in self:
            '''
                ('not_available', 'Not Available'),
                ('free', 'Available'),
                ('reserve', 'Reserved'),
                ('occupied', 'Occupied'),
            '''
            result = {}
            result['stock'] = product_id.qty_available
            if product_id:
                if product_id.qty_available > 1:
                    result['status'] = "free"
                    return result
                    
                rental_schedule = self.env['sale.rental.schedule'].search([
                    ('product_id','=',product_id.id),
                    ('rental_status','in',['pickup','return']),
                    ('report_line_status','in',['reserved','pickedup']),
                    ('return_date','>', start_date),
                    ('pickup_date','<', end_date),
                ], limit=1)
                if rental_schedule:
                    # result['status'] = "reserve" if rental_schedule.rental_status == 'pickup' else "occupied"
                    result['status'] = "reserve" if rental_schedule.report_line_status == 'reserved' else "occupied"
                    result['order_id'] = rental_schedule.order_id.id
                    result['pickup_date'] = rental_schedule.pickup_date
                    result['return_date'] = rental_schedule.return_date
                    result['detail'] = "oleh {partner_name} ({pickup_date} - {return_date}), ref : {order_name}".format(
                        partner_name = rental_schedule.partner_id.name,
                        pickup_date = (rental_schedule.pickup_date + timedelta(hours=7)).strftime("%d %b %Y %H:%M:%S"),
                        return_date = (rental_schedule.return_date + timedelta(hours=7)).strftime("%d %b %Y %H:%M:%S"),
                        order_name = rental_schedule.order_id.name,
                    )
                else:
                    if product_id.qty_available == 1 or product_id.qty_in_rent >= 1:
                        result['status'] = "free"
                    else:
                        result['status'] = "not_available"
                return result

    # roll vendor
    # vendor yang dipilih pindah kebawah
    def roll_vendor(self,partner_id):
        for record in self:
            if record.seller_ids and record.seller_ids.filtered(lambda x : x.name.id == partner_id):
                sequence = 1
                picked_seller = record.seller_ids.filtered(lambda x : x.name.id == partner_id)[0]
                for seller in record.seller_ids:
                    if seller.id != picked_seller.id:
                        seller.sequence = sequence
                        sequence += 1
                picked_seller.sequence = sequence
                
                # sequence = 1
                # first_seller = record.seller_ids[0]
                # for seller in record.seller_ids[1:]:
                #     seller.sequence = sequence
                #     sequence += 1
                # first_seller.sequence = sequence

    # vendor yang dipilih pindah ke atas
    def roll_vendor_rollback(self,partner_id):
        for record in self:
            if record.seller_ids and record.seller_ids.filtered(lambda x : x.name.id == partner_id):
                sequence = 1
                picked_seller = record.seller_ids.filtered(lambda x : x.name.id == partner_id)[0]
                picked_seller.sequence = sequence
                sequence += 1
                for seller in record.seller_ids:
                    if seller.id != picked_seller.id:
                        seller.sequence = sequence
                        sequence += 1


                # sequence = 1
                # last_seller = record.seller_ids[len(record.seller_ids) - 1]
                # last_seller.sequence = sequence
                # sequence += 1
                # for seller in record.seller_ids.filtered(lambda x: x.id != last_seller.id):
                #     seller.sequence = sequence
                #     sequence += 1
                        
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