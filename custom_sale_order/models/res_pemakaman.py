from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class resPemakaman(models.Model):
    _name = "res.pemakaman"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Pemakaman"

    name = fields.Char('Nama TPU', required=True)
    wilayah_id = fields.Many2one('res.pemakaman.wilayah', string='Wilayah')
    wilayah = fields.Selection([
        ('Jakarta Barat', 'Jakarta Barat'),
        ('Jakarta Pusat', 'Jakarta Pusat'),
        ('Jakarta Selatan', 'Jakarta Selatan'),
        ('Jakarta Timur', 'Jakarta Timur'),
        ('Jakarta utara', 'Jakarta utara'),
    ], string='Wilayah')
    daerah = fields.Selection([
        ('jabodetabek', 'JABODETABEK'),
        ('luar jabodetabek', 'LUAR JABODETABEK'),
    ], string='Daerah')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        res = super(resPemakaman, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        return super(resPemakaman, self).write(vals)

class resPemakamanWilayah(models.Model):
    _name = "res.pemakaman.wilayah"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Pemakaman"

    name = fields.Char('Nama Wilayah', required=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        res = super(resPemakamanWilayah, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).upper()
        return super(resPemakamanWilayah, self).write(vals)