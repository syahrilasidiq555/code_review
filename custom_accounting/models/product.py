from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_cogs_inv = fields.Boolean(string="COGS in Invoice ?", default=False)