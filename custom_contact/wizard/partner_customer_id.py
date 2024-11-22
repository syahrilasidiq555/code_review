# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime

class res_partner_customerid_wizard(models.TransientModel):
    _name = 'res.partner.customerid.wizard'

    partner_id = fields.Many2one('res.partner', string='Partner')
    customer_id = fields.Char(string='Customer ID')
    customer_id_new = fields.Char(string='New Customer ID')

    def gaskeun(self):
        self.partner_id.sudo().write({
            'customer_id': self.customer_id_new
        })