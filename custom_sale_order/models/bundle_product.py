from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class BundleProduct(models.Model):
    _name = "bundle.product"

    name = fields.Many2one('product.template', string="Product")
    ni_quantity = fields.Integer(string="Quantity", default=1)
    ni_product_id = fields.Many2one('product.template', string="Product Id")
    ni_uom_id = fields.Many2one('uom.uom', 'Unit of Measure ')

    type = fields.Selection([
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ], string='Type', required=True)
    is_konsinyasi = fields.Boolean(string="is Konsinyasi")


    rent_duration = fields.Integer('Rent Duration', default=0)
    rent_unit = fields.Selection([
        ('hour', 'Jam'),
        ('day', 'Hari'),
        ('week', 'Minggu'),
        ('month', 'Bulan'),
    ], string='Rent UOM', default='day')
    price = fields.Float('Total Price', digits='Product Price')

    @api.onchange('name')
    def _onchange_name(self):
        for record in self:
            if record.name.ni_is_product_pack:
                raise ValidationError("You cannot select Pack Product in product list!")

            if record.name.rent_ok:
                record.type = 'rent'
                record.price = 1
                record.rent_duration = 1
                record.is_konsinyasi = record.name.is_konsinyasi
                for rent in record.name.rental_pricing_ids:
                    record.rent_duration = rent.duration
                    record.rent_unit = rent.unit
                    record.price = rent.price
                    break
            else:
                record.price = record.name.list_price 
                record.type = 'sale'
                record.is_konsinyasi = record.name.is_konsinyasi

    @api.onchange('type')
    def _onchange_type(self):
        for record in self:
            if record.name:
                if not record.name.rent_ok and not record.name.sale_ok:
                    raise ValidationError("Product that you pick cannot be sold or rented, please check on product form before you select the product!")
                if record.type == 'sale' and not record.name.sale_ok:
                    raise ValidationError("This product cannot be sold")
                
                if record.type == 'rent' and not record.name.rent_ok:
                    raise ValidationError("This product cannot be rented")


    @api.model
    def create(self, vals):

        if vals.get('name'):
            product_id = self.env['product.template'].browse(vals.get('name'))
            vals.update({'ni_uom_id': product_id.uom_id.id})
        return super(BundleProduct, self).create(vals)



    # product yang diisi di bundle product tidak boleh sama
    @api.constrains('name')
    def _constrains_product(self):
        for record in self:
            # validasi produk sama
            same_product = self.env[record._name].search([
                ('ni_product_id','=',record.ni_product_id.id),
                ('name','=',record.name.id),
                ('id','!=',record.id),
            ])
            if same_product:
                raise UserError("You already insert this product to bundle product table.\n\nProduct: {product_name}".format(
                    product_name = record.name.name
                ))
            
            # validasi input produk ruang semayam lebih dari 1
            ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            if record.name.categ_id.id == ruang_semayam_category_id.id:
                bundle_product = self.env[self._name].search([
                    ('id','!=',record.id),
                    ('ni_product_id','=',record.ni_product_id.id),
                    ('name.categ_id','=',ruang_semayam_category_id.id)
                ])
                if bundle_product:
                    message = "Ruang semayam telah ditambahkan sebelumnya ({product_name}).\n Tidak boleh menambahkan ruang semayam lebih dari satu!".format(
                        product_name = bundle_product[0].name.name
                    )
                    raise UserError(message)