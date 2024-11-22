# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    method_period = fields.Selection(selection_add=[('-1', 'Hari')])