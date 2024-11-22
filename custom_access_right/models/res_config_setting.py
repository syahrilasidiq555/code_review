from odoo import models, fields, api

import ast

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_default_not_allowed_groups_ids(self):
        ids = []
        if self.env.ref('custom_access_right.group_cs_view_amount'):
            ids.append(self.env.ref('custom_access_right.group_cs_view_amount').id)
        if self.env.ref('custom_access_right.group_purchase_view_amount'):
            ids.append(self.env.ref('custom_access_right.group_purchase_view_amount').id)
        if self.env.ref('custom_access_right.group_inventory_view_amount'):
            ids.append(self.env.ref('custom_access_right.group_inventory_view_amount').id)
        if self.env.ref('custom_access_right.group_sale_order_view_amount'):
            ids.append(self.env.ref('custom_access_right.group_sale_order_view_amount').id)
        return self.env['res.groups'].search([('id', 'in', ids)]).ids

    not_allowed_groups_ids = fields.Many2many("res.groups",
        "res_configs_groups",
        "group_id",
        "config_setting_id", string='Grup yang tidak dapat diedit selain oleh group Administration/Setting', default=_get_default_not_allowed_groups_ids)    
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        group_ids = self.env['ir.config_parameter'].sudo().get_param('custom_access_right.not_allowed_groups_ids')
        if group_ids:
            res.update(
                not_allowed_groups_ids=[(6, 0, ast.literal_eval(group_ids))],
            )
        return res
    
    # @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('custom_access_right.not_allowed_groups_ids', self.not_allowed_groups_ids.ids)
    