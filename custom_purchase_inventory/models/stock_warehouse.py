from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    user_incharge_id = fields.Many2one('res.users', string='Person In Charge', tracking=True)