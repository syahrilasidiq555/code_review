from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'


    # kasih constraints kalau ingin tambah line vendor lagi
    # untuk barang dari warehouse konsinyasi hanya bisa diisi 1 vendor/supplier untuk 1 product
    # ** Error : pada saat confirm PO di vendor yang berbeda (konsinyasi)
    @api.constrains('name')
    def _constrains_name_res_partner(self):
        for record in self:
            # kalau sellernya sama
            vendors = self.env[record._name].search([
                ('id','!=',record.id),
                ('product_tmpl_id','=',record.product_tmpl_id.id),
                ('name','=',record.name.id)
            ])
            if vendors:
                raise UserError("Anda tidak bisa memilih Vendor / Seller yang sama!\n\n Vendor : {partner_name}".format(
                    partner_name = record.name.name
                ))
            
            # barang konsinyasi hanya boleh dimiliki oleh 1 vendor
            # untuk mengatasi kebingunan stock di stock konsinyasi
            if record.product_tmpl_id.is_konsinyasi:
                vendors = self.env[record._name].search([
                    ('id','!=',record.id),
                    ('product_tmpl_id','=',record.product_tmpl_id.id)
                ])
                if vendors:
                    # barang ini belongs to vendor X, bikin product baru
                    raise UserError("Produk ({product_name}) merupakan produk dari {vendor_name} dalam konsinyasi Warehouse, silahkan buat produk baru!".format(
                        product_name = record.product_tmpl_id.name,
                        vendor_name = vendors[0].name.name
                    ))
                