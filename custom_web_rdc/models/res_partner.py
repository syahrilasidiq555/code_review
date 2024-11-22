# from attr import field
from unicodedata import category
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_hospital = fields.Boolean(string="Rumah Sakit", default=False, store=True)
    hospital_id = fields.Many2one('res.hospital', string='Asal Jenazah')