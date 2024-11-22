# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime

class AssetChangeLocation(models.TransientModel):
    _name = 'asset.change.location'

    asset_id = fields.Many2one('account.asset', string="Asset")
    location_origin_id = fields.Many2one('account.asset.location', string='Origin Location', readonly=True)
    location_id = fields.Many2one('account.asset.location', string='Move to Location', domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    move_date = fields.Date(string="Move Date", default=fields.Datetime.now, required=True)
    employee_location_id = fields.Many2one('hr.employee', string='Employee', ondelete='restrict')
    
    def action_confirm(self):
        if self.location_id:
            self.asset_id.write({'state': 'to_approve_location'})
            # self.asset_id.write({
            #     'location_id': self.location_id.id,
            #     })
            # self.asset_id.write({
            #     'code_name': self.asset_id.get_code_name(),
            #     })

            self.env['account.asset.location.history'].create({
                'asset_id': self.asset_id.id,
                'location_origin_id': self.location_origin_id.id,
                'location_id': self.location_id.id,
                'employee_location_id': self.employee_location_id.id,
                'move_date': self.move_date,
            })
        else:
            raise ValidationError("Move to Location must be selected.")