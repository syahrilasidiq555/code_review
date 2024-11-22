from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_specific_warehouse_group = fields.Boolean(compute='_compute_access_specific_warehouse_group', string='Access Specific Warehouse')
    @api.depends('groups_id','groups_count')
    def _compute_access_specific_warehouse_group(self):
        for record in self:
            record.is_specific_warehouse_group = False
            specific_warehouse_group = self.env.ref('custom_purchase_inventory.group_inventory_specific_warehouse_loc')
            if record.groups_id.filtered(lambda x: x.id == specific_warehouse_group.id):
                record.is_specific_warehouse_group = True

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