from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    main_warehouse_id = fields.Many2one('stock.warehouse', string='Main Warehouse', default=1, config_parameter='custom_sale_order.main_warehouse_id')
    kons_warehouse_id = fields.Many2one('stock.warehouse', string='Konsinyasi Warehouse', config_parameter='custom_sale_order.kons_warehouse_id')