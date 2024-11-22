# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    product_desc = fields.Text('Product Desc')
    product_qty = fields.Float('Qty')
    project_id = fields.Many2one('project.project', readonly=True)
    state = fields.Selection(selection_add=[
        ('draft_quot','Draft Quotation'),
        ('to approve','To Approve'),
        ('draft','Approved Quotation'), 
        ('sent',),
    ], default="draft_quot")
    


    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['product_qty'] = "l.product_uom_qty"
        res['product_desc'] = "l.name"
        res['project_id'] = "l.project_id"
        return res

    # def _from_sale(self):
    #     res = super()._from_sale()
    #     res += """
    #         LEFT JOIN account_move am on am.so_id = s.id"""
    #     return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            l.product_uom_qty,
            l.name,
            l.project_id
        """
        return res
