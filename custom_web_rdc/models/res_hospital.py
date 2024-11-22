from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime

class ResHospital(models.Model):
    _name = "res.hospital"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Rumah Sakit"

    name = fields.Char(string='Nama', required=True)
    
    partner_id = fields.Many2one('res.partner', string='Contact')
    phone = fields.Char(related="partner_id.phone", readonly=False, string='No. Telepon')
    street = fields.Char(related="partner_id.street", readonly=False, string='Alamat')
    city = fields.Char(related="partner_id.city", readonly=False, string='Kota')
    zip = fields.Char(related="partner_id.zip", readonly=False, string='Kode Pos')
    state_id = fields.Many2one(related="partner_id.state_id", readonly=False, comodel_name='res.country.state', string='Provinsi', domain="[('country_id','=?',country_id)]")
    country_id = fields.Many2one(related="partner_id.country_id", readonly=False, comodel_name='res.country', string='Country', default=100)


    @api.model
    def create(self, values):
        self.clear_caches()
        if values.get('name'):
            partner_id = self.env['res.partner'].create({
                'is_hospital':True,
                'name': values.get('name') if values.get('name') else None,
                # 'phone': values.get('phone') if values.get('phone') else None,
                # 'street': values.get('street') if values.get('street') else None,
                # 'city': values.get('city') if values.get('city') else None,
                # 'zip': values.get('zip') if values.get('zip') else None,
                # 'state_id': values.get('state_id') if values.get('state_id') else None,
                # 'country_id': values.get('country_id') if values.get('country_id') else None,
            })
            values['partner_id'] = partner_id.id
        res = super(ResHospital,self).create(values)
        return res