from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 


class BundleWizard(models.TransientModel):
    _name = "bundle.wizard"

    def _get_default_pickup_return_date(tipe):
        pickup_date = datetime.now()
        # print("===============================")
        # print(pickup_date)
        return_date = datetime.now() + timedelta(days=2)
        # hour = 0 if (pickup_date+timedelta(hours=7)).hour >= 23 else pickup_date.hour
        
        # if hour == 0:
        #     pickup_date = pickup_date.replace(hour=0,minute=0,second=0)
        #     pickup_date += timedelta(days=1,hours=-7)
        #     return_date = pickup_date + timedelta(days=2)
        #     # return_date = return_date.replace(hour=23, minute=59, second=59)
        #     # print("++++++++++++++++++")
        #     # print(pickup_date)

        if tipe == 'pickup':
            return pickup_date
        elif tipe == 'return':
            return return_date.replace(hour=23, minute=59, second=59) - timedelta(hours=7)

    ni_pack_name = fields.Many2one('product.template', string="Paket", required=True,)

    
    def _get_ruang_semayam_id_domain(self):
        domain = [('1','=',1)]
        ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
        if ruang_semayam_category_id:
            domain = [('product_tmpl_id.categ_id','=',ruang_semayam_category_id.id)]
        return domain

    template_ruang_semayam_id = fields.Many2one('product.template', string='Ruang Semayam')
    ruang_semayam_id = fields.Many2one('product.product', string='Ruang Semayam', domain=_get_ruang_semayam_id_domain)
    pickup_date = fields.Datetime(string="Tanggal Pickup", default=_get_default_pickup_return_date(tipe="pickup"))
    return_date = fields.Datetime(string="Tanggal Return", default=_get_default_pickup_return_date(tipe="return"))

    rental_status = fields.Selection([
        ('not_available', 'Not Available'),
        ('free', 'Available'),
        ('reserve', 'Reserved'),
        ('occupied', 'Occupied'),
    ], compute='_compute_list_price', string='Status Rental')
    other_cust_pickup_date = fields.Datetime(string="Tanggal Pickup", compute='_compute_list_price')
    other_cust_return_date = fields.Datetime(string="Tanggal Return", compute='_compute_list_price')
    rental_status_detail = fields.Char(compute='_compute_list_price', string='Status Rental')

    @api.depends('ruang_semayam_id','return_date','pickup_date')
    def _compute_list_price(self):
        for record in self:
            record.rental_status = None
            record.other_cust_pickup_date = False
            record.other_cust_return_date = False
            record.rental_status_detail = None
            if record.ruang_semayam_id and record.pickup_date and record.return_date:
                rental_status_json = record.ruang_semayam_id.product_tmpl_id.get_rental_status_info(
                    product_id = record.ruang_semayam_id,
                    start_date = record.pickup_date,
                    end_date = record.return_date,
                )
                # record.rental_status_json = str(rental_status_json)
                record.rental_status = rental_status_json.get('status')
                record.rental_status_detail = "{status} {detail}".format(
                    status= dict(self._fields['rental_status'].selection).get(record.rental_status),
                    detail= rental_status_json.get('detail') if rental_status_json.get('detail') else ""
                )
                record.other_cust_pickup_date = rental_status_json.get('pickup_date')
                record.other_cust_return_date = rental_status_json.get('return_date')
    
    pelebaran_ruangan = fields.Boolean(related="ni_pack_name.pelebaran_ruangan")
    jumlah_voucher_parkir = fields.Integer(related="ni_pack_name.jumlah_voucher_parkir")
    # rel_list_price = fields.Float(related="ni_pack_name.list_price", string='Harga')
    rel_list_price = fields.Float(compute='_compute_diff_semayam_price', string='Harga')
    diff_semayam_price = fields.Char(compute='_compute_diff_semayam_price', string='Harga Selisih Columbarium')
    
    @api.depends('ni_pack_name','template_ruang_semayam_id','ruang_semayam_id','pickup_date','return_date')
    def _compute_diff_semayam_price(self):
        for record in self:
            rel_list_price = record.ni_pack_name.list_price if record.ni_pack_name else 0
            record.diff_semayam_price = record.get_difference_product_price() if record.ruang_semayam_id else 0
            record.rel_list_price = float(rel_list_price) + float(record.diff_semayam_price)

    rel_currency_id = fields.Many2one(related="ni_pack_name.currency_id", string='Mata Uang')
    ni_quantity = fields.Integer(string="Quantity", default=1)

    product_ids = fields.One2many('bundle.wizard.line', 'bundle_wizard_id', string='Product List')
    product_rent_ids = fields.One2many('bundle.wizard.line.rent', 'bundle_wizard_id', string='Product Rent List')

    product_accesories_ids = fields.One2many('bundle.wizard.line.accesories', 'bundle_wizard_id', string='Aksesoris')

    is_variant_selected = fields.Boolean(compute='_compute_is_variant_selected', string='is Variant Selected')
    
    @api.depends('product_ids','product_rent_ids')
    def _compute_is_variant_selected(self):
        for record in self:
            record.is_variant_selected = True

        sale_variant_not_selected = record.product_ids.filtered(lambda x: x.product_variant_count > 1 and not x.variant_id)
        rental_variant_not_selected = record.product_rent_ids.filtered(lambda x: x.product_variant_count > 1 and not x.variant_id)

        if sale_variant_not_selected or rental_variant_not_selected:
            record.is_variant_selected = False

    @api.constrains('ruang_semayam_id','pickup_date','return_date')
    def _constrains_ruang_semayam_id(self):
        for record in self:
            if record.ruang_semayam_id and record.pickup_date and record.return_date:
                if record.pickup_date > record.return_date:
                    raise ValidationError("Tanggal mulai Ruang Semayam tidak boleh lebih dari tanggal berakhir!")
                
                date_diff = record.return_date - record.pickup_date
                if date_diff.days >= 3 and round(date_diff.seconds / 3600,0) > 0 :
                    raise ValidationError("Jumlah hari pada Ruang Semayam tidak boleh lebih dari 3 hari ! \n\n Total : {total_selisih}".format(
                        total_selisih = "%s Hari %s Jam" % (date_diff.days, int(round(date_diff.seconds / 3600,0)))
                    ))


    @api.onchange('ni_pack_name')
    def _onchange_ni_pack_name(self):
        for record in self:
            ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            record.product_ids = None
            record.product_rent_ids = None
            if record.ni_pack_name:
                product_ids = record.ni_pack_name.ni_bundle_product_ids.filtered(lambda x: x.type == 'sale')
                product_rent_ids = record.ni_pack_name.ni_bundle_product_ids.filtered(lambda x: x.type == 'rent' and x.name.categ_id.id != ruang_semayam_category_id.id)
                ruang_semayam_ids = record.ni_pack_name.ni_bundle_product_ids.filtered(lambda x: x.name.categ_id.id == ruang_semayam_category_id.id)
                record.template_ruang_semayam_id = ruang_semayam_ids[0].name.id if ruang_semayam_ids else False
                record.ruang_semayam_id = False

                products = []
                for product in product_ids:
                    products.append([0,0,{
                        'product_id' : product.name.id,
                        'qty' : product.ni_quantity,
                        'price':product.price,
                        'is_konsinyasi':product.is_konsinyasi,
                    }])
                record.product_ids = products

                rent_products = []
                for product in product_rent_ids:
                    # raise UserError(str(self.env.context.get('tanggal_kedatangan')))
                    pickup_date = datetime.now().replace(minute=00, hour=00, second=00) - timedelta(hours=7) # dikurangi 7 jam karena timezone
                    if self.env.context.get('tanggal_kedatangan'):
                        pickup_date = datetime.strptime(self.env.context.get('tanggal_kedatangan'), "%Y-%m-%d %H:%M:%S")

                    # pickup_date = datetime.now().replace(minute=00, hour=00, second=00)
                    hours = product.rent_duration if product.rent_unit == 'hour' else 0
                    days = product.rent_duration if product.rent_unit == 'day' else 0
                    days = product.rent_duration * 7 if product.rent_unit == 'week' else days
                    # days = product.rent_duration * 30 if product.rent_unit == 'month' else days
                    return_date = pickup_date + timedelta(days=days, hours=hours)
                    
                    if product.rent_unit == 'month':
                        return_date = pickup_date + timedelta(hours=hours) + relativedelta(months=product.rent_duration)

                        # kalau columbarium kurang 1 hari
                        columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
                        if product.name.categ_id.id == columbarium_category_id.id:
                            return_date = return_date + timedelta(days=-1)

                    rent_products.append([0,0,{
                        'product_id' : product.name.id,
                        'qty' : product.ni_quantity,
                        'rent_duration':product.rent_duration,
                        'rent_unit':product.rent_unit,
                        'pickup_date' :  pickup_date,
                        'return_date' :  return_date,
                        'price':product.price,
                        'price_default':product.price,
                        'is_konsinyasi':product.is_konsinyasi,
                    }])
                record.product_rent_ids = rent_products

    def validate_variant(self):
        for record in self:
            if record.template_ruang_semayam_id:
                if not record.ruang_semayam_id:
                    raise ValidationError("Anda harus memilih ruang semayam terlebih dahulu!")
                if not record.pickup_date or not record.return_date:
                    raise ValidationError("Anda harus memilih tanggal dan jam ruang semayam terlebih dahulu!")

            if not record.is_variant_selected:
                message = "Anda belum memilih variant untuk produk berikut ini :\n\n"
                sale_variant_not_selected = record.product_ids.filtered(lambda x: x.product_variant_count > 1 and not x.variant_id)
                rental_variant_not_selected = record.product_rent_ids.filtered(lambda x: x.product_variant_count > 1 and not x.variant_id)

                i = 1
                for sale in sale_variant_not_selected:
                    message += "{i}. {product}\n".format(
                        i = i,
                        product = sale.product_id.name
                    )
                    i+= 1

                for rental in rental_variant_not_selected:
                    message += "{i}. {product}\n".format(
                        i = i,
                        product = rental.product_id.name
                    )
                    i+= 1

                raise ValidationError(message)

            # validasi status rental not available
            # if record.rental_status == 'not_available':
            #     raise ValidationError("Ruang semayam yang dipilih tidak tersedia!")
            # elif record.rental_status in ['reserved','occupied'] and ((record.other_cust_return_date >= record.pickup_date) and (record.other_cust_pickup_date <= record.return_date)):
            #     raise ValidationError("Ruang semayam yang dipilih tidak tersedia, silahkan perhatikan status rental pada tiap2 ruangan!")

    def create_park_voucher(self,active_id):
        for record in self:
            voucher_parkir_obj = self.env['parking.voucher']
            sale_order = self.env['sale.order'].browse(active_id)
            for i in range(0,record.jumlah_voucher_parkir):
                voucher_parkir_obj.create({
                    'date': sale_order.partner_id.tanggal_kedatangan if sale_order and sale_order.partner_id.tanggal_kedatangan else datetime.now(),
                    # 'date_out': sale_order.tanggal_keluar if sale_order and sale_order.tanggal_keluar else datetime.now().date(),
                    'sale_order_id': active_id
                })

    def get_difference_product_price(self):
        for record in self:
            price = 0
            # get selisih price
            if record.ruang_semayam_id.product_tmpl_id.id != record.template_ruang_semayam_id.id:
                # get ruang semayam default price
                product_default_price_unit = 0
                packet_line = record.ni_pack_name.ni_bundle_product_ids.filtered(lambda x : x.name.id == record.template_ruang_semayam_id.id)
                if packet_line:
                    product_default_price_unit = packet_line.price

                # get other product price
                list_price = 0
                if record.ruang_semayam_id and record.pickup_date and record.return_date:
                    list_price = record.ruang_semayam_id.product_tmpl_id.get_rental_list_price(
                        product_id = record.ruang_semayam_id,
                        start_date = (record.pickup_date + timedelta(hours=7)).date(),
                        end_date = (record.return_date + timedelta(days=1, hours=7)).date(),
                        exclude_hour = True,
                )
                    
                difference = (list_price * 1) - product_default_price_unit
                price = difference if difference > 0 else 0
                # raise UserError(f'default: {product_default_price_unit}\n\ncurrent: {list_price}\n\ndiff: {difference}')
                return price

    def add_pack(self):
        self.validate_variant()

        active_id = self.env.context.get('active_id')

        self.create_park_voucher(active_id)

        product_id = self.env['product.product'].search([('product_tmpl_id', '=', self.ni_pack_name.id)])

        if self.env.context.get('active_model') == 'sale.order':
            sale_order_line_obj = self.env['sale.order.line']
            
            # buat section di sale order line
            parent = sale_order_line_obj.create({
                'order_id': active_id,
                'product_id': product_id.id,
                'paket_id':product_id.product_tmpl_id.id,
                'name': '[Bundle] {product_name}'.format(
                    product_name = product_id.name,
                ),
                'product_uom_qty': 1, 
                'price_unit': product_id.product_tmpl_id.list_price,
                'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')),
                # 'product_warehouse_id':product_id.product_tmpl_id.default_stock_warehouse_id.id,
            })
            
            if len(self.product_rent_ids) >=1 or self.ruang_semayam_id:
                self.env['sale.order'].browse(active_id).write({
                    'is_rental_order':True,
                    'rental_status':'draft'
                })

            if self.ruang_semayam_id:
                price = self.get_difference_product_price()

                values = {
                    'order_id': active_id,
                    'product_id': self.ruang_semayam_id.id,
                    'name': 'RENTAL - {product_name} ({bundle_name})\n{pickup_date} to {return_date}'.format(
                        product_name = self.ruang_semayam_id.display_name,
                        bundle_name = product_id.name,
                        pickup_date = (self.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                        return_date = (self.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    ),
                    'product_uom_qty': 1, 
                    'price_unit': price,
                    'tax_id': None,
                    'parent_id': parent.id,
                    'pengganti_id': parent.id,
                    'is_rental': True,
                    'reservation_begin': self.pickup_date,
                    'pickup_date': self.pickup_date,
                    'return_date': self.return_date,
                    # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not self.ruang_semayam_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'product_warehouse_id':self.ruang_semayam_id.product_tmpl_id.default_stock_warehouse_id.id if not self.ruang_semayam_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    
                }
                sale_order_line_obj.create(values)
            
            for product_rent in self.product_rent_ids:
                produk = self.env['product.product'].search([('product_tmpl_id', '=', product_rent.product_id.id)], limit=1)
                if produk:
                    values = {
                        'order_id': active_id,
                        'product_id': produk.id if not product_rent.variant_id else product_rent.variant_id.id,
                        'name': 'RENTAL - {product_name} ({bundle_name})\n{pickup_date} to {return_date}'.format(
                            product_name = product_rent.product_id.name,
                            bundle_name = product_id.name,
                            pickup_date = (product_rent.pickup_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                            return_date = (product_rent.return_date+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                        ),
                        'product_uom_qty': product_rent.qty * self.ni_quantity, #kalikan qty di dalam 1 bundle dan total paket yang dipilih
                        'price_unit': 0,
                        'tax_id': None,
                        'parent_id': parent.id,
                        'is_rental': True,
                        'reservation_begin': product_rent.pickup_date,
                        'pickup_date': product_rent.pickup_date,
                        'return_date': product_rent.return_date,
                        # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not product_rent.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                        'product_warehouse_id':produk.product_tmpl_id.default_stock_warehouse_id.id if not product_rent.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    }
                    sale_order_line_obj.create(values)

            for product in self.product_ids:
                produk = self.env['product.product'].search([('product_tmpl_id', '=', product.product_id.id)], limit=1)
                if produk:
                    values = {
                        'order_id': active_id,
                        'product_id': produk.id if not product.variant_id else product.variant_id.id,
                        'name': '{product_name} ({bundle_name})'.format(
                            product_name = product.product_id.name,
                            bundle_name = product_id.name,
                        ),
                        'product_uom_qty': product.qty * self.ni_quantity, #kalikan qty di dalam 1 bundle dan total paket yang dipilih
                        'price_unit': 0,
                        'tax_id': None,
                        'parent_id': parent.id,
                        # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not product.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                        'product_warehouse_id':produk.product_tmpl_id.default_stock_warehouse_id.id if not product.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    }
                    sale_order_line_obj.create(values)

            for accessory in self.product_accesories_ids:
                values = {
                    'order_id': active_id,
                    'product_id': accessory.product_id.id,
                    'name': '{product_name} ({bundle_name} - Aksesoris)'.format(
                        product_name = accessory.product_id.name,
                        bundle_name = product_id.name,
                    ),
                    'product_uom_qty': accessory.qty,
                    'price_unit': accessory.list_price,
                    # 'tax_id': None,
                    'tax_id': [tax.id for tax in accessory.product_id.product_tmpl_id.taxes_id],
                    # 'parent_id': parent.id,
                    # 'product_warehouse_id':int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not product.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                    'product_warehouse_id':accessory.product_id.product_tmpl_id.default_stock_warehouse_id.id if not accessory.product_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id')),
                }
                sale_order_line_obj.create(values)

# untuk Page Sale
class BundleWizardLine(models.TransientModel):
    _name = "bundle.wizard.line"

    bundle_wizard_id = fields.Many2one('bundle.wizard', string='Bundle')
    product_id = fields.Many2one('product.template', string='Product')
    product_variant_count = fields.Integer(related="product_id.product_variant_count")
    variant_id = fields.Many2one('product.product', string='Varian', domain="[('product_tmpl_id','=',product_id)]")
    qty = fields.Integer('Quantity')
    price = fields.Float('Total Price', digits='Product Price')
    is_konsinyasi = fields.Boolean(string="is Konsinyasi")

# untuk Page Rental
class BundleWizardLineRent(models.TransientModel):
    _name = "bundle.wizard.line.rent"
    _inherit = "bundle.wizard.line"

    variant_id = fields.Many2one(domain="[('product_tmpl_id','=',product_id),('qty_available','>=',1)]")
    rent_duration = fields.Integer('Rent Duration', default=0)
    rent_unit = fields.Selection([
        ('hour', 'Jam'),
        ('day', 'Hari'),
        ('week', 'Minggu'),
        ('month', 'Bulan'),
    ], string='Rent UOM', default='day')
    price_default = fields.Float('Price Default', digits='Product Price')
    pickup_date = fields.Datetime(string='Pickup Date')
    return_date = fields.Datetime(string='Return Date')



    # get price based on rental price
    @api.onchange('pickup_date','return_date')
    def _onchange_pickup_return_date(self):
        for record in self:
            price_per_uom = (record.price_default / record.qty) / record.rent_duration
            date_diff = record.return_date - record.pickup_date

            if record.rent_unit == 'hour':
                price = 0
                if date_diff.days:
                    price = (date_diff.days * 24) * price_per_uom
                record.price = price + round(date_diff.seconds/3600,0) * price_per_uom
            elif record.rent_unit == 'day':
                record.price = date_diff.days * price_per_uom

# untuk page Accesories
class BundleWizardLineAccesories(models.TransientModel):
    _name = "bundle.wizard.line.accesories"

    bundle_wizard_id = fields.Many2one('bundle.wizard', string='Bundle')

    product_id = fields.Many2one('product.product', string='Product')
    list_price = fields.Float(related="product_id.list_price", string="Price Unit")
    qty = fields.Integer(string='Quantity', default=1)
    price = fields.Float('Total Price', digits='Product Price', compute='_compute_price')

    @api.depends('product_id','qty','list_price')
    def _compute_price(self):
        for record in self:
            record.price = record.list_price * record.qty
