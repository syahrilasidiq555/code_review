# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.osv.expression import AND


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'

    @api.depends('route_id','product_tmpl_id')
    def _compute_show_vendor(self):
        res = super(ProductReplenish, self)._compute_show_vendor()
        for rec in self:
            if rec.product_tmpl_id.purchase_request:
                rec.show_vendor = False 
        return res
    

    # purchase_stock.route_warehouse0_buy

    def launch_replenishment(self):
        res = super(ProductReplenish, self).launch_replenishment()
        for rec in self:
            route_buy_id = 0
            try:
                route_buy_id = self.env.ref('purchase_stock.route_warehouse0_buy').id
            except:
                pass

            if rec.product_tmpl_id.purchase_request and rec.route_id.id == route_buy_id:
                action = self.env.ref('purchase_request.purchase_request_form_action')
                links = [{
                    'label': 'Purchase Request',
                    'url': f'#action={action.id}&model={action.res_model}&view_type=list'
                }] if action else False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Purchase Request have been generated'),
                        'message': '%s',
                        'links': links,
                        'sticky': False,
                        'next': {
                            'type': 'ir.actions.act_window_close',
                            'infos': {'done': True},
                        }
                    }
                }
        return res