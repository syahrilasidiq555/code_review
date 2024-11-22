# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    location_id = fields.Many2one('account.asset.location', string='Location', domain="[('company_id', '=', company_id)]")
    merek_id = fields.Many2one('account.asset.merek', string='Merek', domain="[('company_id', '=', company_id)]")
    