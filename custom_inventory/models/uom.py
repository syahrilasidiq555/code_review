# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class UoM(models.Model):
    _inherit = 'uom.uom'

    rounding = fields.Float(default=1, digits="Product Unit of Measure")