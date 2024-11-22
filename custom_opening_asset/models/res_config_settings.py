from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    compute_asset_based_opening = fields.Boolean(string='Compute Asset based Opening', related='company_id.compute_asset_based_opening', readonly=False)
