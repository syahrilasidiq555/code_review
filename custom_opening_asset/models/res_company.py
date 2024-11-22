from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    compute_asset_based_opening = fields.Boolean(string='Compute Asset based Opening')
