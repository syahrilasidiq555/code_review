from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta,date

import json

class ChoosePartnerWizard(models.TransientModel):
    _name = 'choose.partner.wizard'
    _description = 'Choose Partner'

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet', readonly=True)
    company_id = fields.Many2one(related='cost_sheet_id.company_id', string='Company', readonly=True)

    cost_sheet_line_id = fields.Many2one('cost.sheet.line', string='Cost Sheet Line')
    vendor_ids = fields.Many2many('res.partner',compute='_compute_vendor_ids', string='Vendor IDS')
    @api.depends('cost_sheet_id','cost_sheet_line_id')
    def _compute_vendor_ids(self):
        for record in self:
            active_id = self.env.context.get('active_id')
            active_model = self.env.context.get('active_model')

            record.vendor_ids = False
            vendor_ids = []
            if record.cost_sheet_line_id.product_id:
                for seller_id in record.cost_sheet_line_id.product_id.seller_ids:
                    vendor_ids.append((4,seller_id.name.id))
            elif active_model == 'purchase.order':
                po = self.env[active_model].browse(active_id)
                for order_line in po.order_line.filtered(lambda x: x.product_id.seller_ids):
                    for seller_id in order_line.product_id.seller_ids:
                        vendor_ids.append((4,seller_id.name.id))

            if vendor_ids:
                record.vendor_ids = vendor_ids

    vendor_id_domain = fields.Char(compute='_compute_vendor_id_domain', string='Vendor Domain')
    @api.depends('vendor_ids','cost_sheet_id','cost_sheet_line_id')
    def _compute_vendor_id_domain(self):
        for record in self:
            almarhums = self.env['res.partner'].search([('is_jenazah','=',True)])
            domain = [
                ('is_jenazah','=',False),
                ('parent_id','not in',almarhums.ids),
                ('id','in',record.vendor_ids.ids),
            ]
            record.vendor_id_domain = json.dumps(domain)
            if record.vendor_ids and record.cost_sheet_line_id:
                domain = [('id','in',record.vendor_ids.ids)]
                record.vendor_id_domain = json.dumps(domain)


    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True, tracking=True, 
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", 
        help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    reason = fields.Text('Alasan Ganti Vendor', required=True)

    def action_choose(self):
        for record in self:
            active_id = self.env.context.get('active_id')
            active_model = self.env.context.get('active_model')
            if record.vendor_id:
                if record.cost_sheet_line_id:
                    record.cost_sheet_line_id.sudo().write({'vendor_id': record.vendor_id.id})
                    record.cost_sheet_id.message_post(body="Changed Vendor : \n" + record.vendor_id.name + " in line " + record.cost_sheet_line_id.name)
                elif active_model == 'purchase.order':
                    cost_sheet_loa = self.env.ref('custom_accounting.cost_sheet_changed_vendor_approval')
                    po = self.env[active_model].browse(active_id)
                    po.partner_id = record.vendor_id
                    po.loa_type = cost_sheet_loa.id if cost_sheet_loa else None
                    if cost_sheet_loa:
                        po.loa_type = cost_sheet_loa.id
                        po._onchange_loa_type()
                    order_lines = po.order_line.filtered(lambda x: x.cost_sheet_line_id)
                    for order_line in order_lines:
                        order_line.cost_sheet_line_id.vendor_id = record.vendor_id
                        order_line.cost_sheet_line_id._onchange_vendor_id()

                        # update harga sesuai vendor
                        for seller in order_line.product_id.product_tmpl_id.seller_ids.filtered(lambda x : x.name.id == record.vendor_id.id):
                            order_line.price_unit = seller.price
                    
                    # set log note
                    po.message_post(body="Alasan ganti vendor : " + str(record.reason))

                    # vendors = [x.cost_sheet_line_id.vendor_id.name for x in cost_sheet_lines]
                    # raise UserError(str(vendors))