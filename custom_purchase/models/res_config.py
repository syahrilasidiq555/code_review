from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_compare_vendor = fields.Boolean("Komparasi Vendor", config_parameter='custom_purchase.is_compare_vendor')
    compare_vendor_amount = fields.Float(config_parameter='custom_purchase.compare_vendor_amount', string="Nilai Komparasi >=", currency_field='company_currency_id', readonly=False)
    min_count_compare_vendor = fields.Integer("Minimal Komparasi", config_parameter='custom_purchase.min_count_compare_vendor')