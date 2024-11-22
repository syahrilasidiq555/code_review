from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2many('stock.warehouse',
        "res_users_warehouse_rel",
        "user_id",
        "stock_warehouse_id", string='Akses Warehouse')
    
    location_ids = fields.Many2many('stock.location',
        "res_users_location_rel",
        "user_id",
        "stock_location_id", string='Akses Lokasi')
    
    # @api.onchange('warehouse_ids')
    # def _onchange_warehouse_ids(self):
    #     for record in self:
    #         if record.warehouse_ids:
    #             location_list = self.env['stock.location'].sudo().search([('warehouse_id','in',record.warehouse_ids.ids)])
    #             if location_list:
    #                 record.location_ids = [(4,loc.id) for loc in location_list] 