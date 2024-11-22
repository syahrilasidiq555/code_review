import logging

from psycopg2 import Error, OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_inventory_history(self):
        self.ensure_one()
        action = {
            'name': _('History'),
            'view_mode': 'list,form',
            'res_model': 'stock.move.line',
            'views': [(self.env.ref('stock.view_move_line_tree').id, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'context': {
                'search_default_inventory': 1,
                'search_default_done': 1,
                'search_default_groupby_partner': 1,
            },
            'domain': [
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id),
                '|',
                    ('location_id', '=', self.location_id.id),
                    ('location_dest_id', '=', self.location_id.id),
            ],
        }
        if self.lot_id:
            action['context']['search_default_lot_id'] = self.lot_id.id
        if self.package_id:
            action['context']['search_default_package_id'] = self.package_id.id
            action['context']['search_default_result_package_id'] = self.package_id.id
        if self.owner_id:
            action['context']['search_default_owner_id'] = self.owner_id.id
        return action
    
    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, out)
        res['date'] = self.inventory_date
        return res