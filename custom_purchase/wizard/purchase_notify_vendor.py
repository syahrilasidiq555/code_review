# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class PurchaseNotifyVendor(models.TransientModel):
    _name = 'purchase.notif.vendor'

    po_id = fields.Many2one('purchase.order', string='Purchase Order')
    desc = fields.Text(string='Deskripsi')
    yes_no = fields.Selection(string='Pilihan', selection=[('yes', 'Akan melakukan komparasi'), ('no', 'Tidak akan melakukan komparasi')])
    alasan = fields.Text(string='Alasan')
    
    def action_confirm(self):
        if self.yes_no == 'no':
            self.po_id.write({
                'yes_no':self.yes_no,
                'alasan':self.alasan
                })
            self.po_id.button_confirm(False)
        else:
            self.po_id.write({
                'yes_no':self.yes_no,
                'alasan':self.alasan
                })

        return