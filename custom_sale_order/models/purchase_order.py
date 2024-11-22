from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

from datetime import datetime

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    cost_sheet_sale_order_id = fields.Many2one(related="cost_sheet_id.sale_order_id", store=True)
    cost_sheet_partner_id = fields.Many2one(related="cost_sheet_id.partner_id", store=True)
    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 
    # BUTTON CONFIRM
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        for record in self:
            # update purchase pricing di tab `Purchase` pada Product Template
            record.action_update_default_purchase_pricing()
            
            # roll vendor
            # record.roll_vendor_product_list()


    # BUTTON CANCEL
    def button_cancel(self):
        last_state  = self.state
        res = super(PurchaseOrder, self).button_cancel()
        
        # rollback rolling vendor
        # for record in self:
        #     if last_state in ['to approve','purchase']:
        #         record.roll_vendor_product_list_rollback()


    ###############################################################
    ##   METHOD
    ############################################################### 
    # untuk button change vendor
    def action_change_vendor(self):
        for record in self:
            result = {
                'name': _('Choose Vendor'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('custom_sale_order.choose_partner_wizard_view').id, 
                'res_model': 'choose.partner.wizard', 
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_cost_sheet_id': record.cost_sheet_id.id,
                    # 'default_cost_sheet_line_id': record.id,
                }
            }
            return result 

    def action_update_default_purchase_pricing(self):
        for record in self:
            for item in record.order_line:
                for seller in item.product_id.seller_ids:
                    if seller.name.id == record.partner_id.id:
                        seller.price = item.price_unit
    
    # roll vendor pada tiap2 product
    # def roll_vendor_product_list(self):
    #     for record in self:
    #         for line in record.order_line:
    #             line.product_id.product_tmpl_id.roll_vendor(record.partner_id.id)

    # # rollback roll vendor pada tiap2 product
    # def roll_vendor_product_list_rollback(self):
    #     for record in self:
    #         for line in record.order_line:
    #             line.product_id.product_tmpl_id.roll_vendor_rollback(record.partner_id.id)
    

    # tombol view cost sheet
    def action_view_cost_sheet(self):
        for record in self:
            result = {
                'name': _("Cost Sheet"),
                'type': 'ir.actions.act_window',
                'res_model': 'cost.sheet',
                'view_mode': 'form',
                'res_id': record.cost_sheet_id.id,
                'context': {
                    'create': False,
                }
            }
            return result
    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cost_sheet_line_id = fields.Many2one('cost.sheet.line', string='Cost Sheet Line')

    # @api.onchange('price_unit','order_id','order_id.currency_id','order_id.date_order')
    def _onchange_price_unit(self):
        for record in self:
            if record.cost_sheet_line_id and record.cost_sheet_line_id.budget_cost_unit != record.price_unit:
                if record.cost_sheet_line_id.currency_id == record.order_id.currency_id:
                    record.cost_sheet_line_id.budget_cost_unit = record.price_unit
                else:
                    converted_price_unit = record.order_id.currency_id._convert(
                        record.price_unit,
                        record.cost_sheet_line_id.currency_id,
                        record.order_id.company_id,
                        record.order_id.date_order,
                    )
                    # raise UserError(converted_price_unit)
                    record.cost_sheet_line_id.budget_cost_unit = converted_price_unit

    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 

    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)
        for record in self:
            record._onchange_price_unit()
        return res
    
    # Fungsi untuk prepare field di account move line pada saat klik create bill di PO
    # tambah field cost sheet line id
    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        
        if self.cost_sheet_line_id:
            res['cost_sheet_line_id'] = self.cost_sheet_line_id.id
        
        return res