# from attr import field
from unicodedata import category
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import email_split, float_is_zero
from itertools import groupby

from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

import calendar
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', '&', '|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_jenazah','=', True), ('is_customer','=',True)]",
        String="Almarhum")
    payment_id = fields.Many2one('account.payment', string="Pembayaran Columbarium", readonly=True, store=True)

    def action_bayar_columnbarium(self):
        if not self.columbarium_ids:
            raise UserError("Tidak ada product columbarium yang perlu dibayarkan.")
        
        result = {
            'name': _('Pembayaran Columbarium'), 
            'view_type': 'form', 
            'view_mode': 'form', 
            'view_id': self.env.ref('custom_accounting.view_pembayaran_columnbarium_wizard').id, 
            'res_model': 'account.payment.columnbarium.wizard', 
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_amount': sum(self.order_line.filtered(lambda x: x.is_columbarium == str(True)).mapped('price_subtotal'))
            }
        }
        return result
        
    def action_view_columnbarium_payment(self):
        result = {
            'name': _('Pembayaran Columbarium'), 
            'view_mode': 'form', 
            'res_model': 'account.payment', 
            'res_id': self.payment_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return result
    
    # KHSUS INVOICE COLUMBARIUM
    def action_view_columnbarium_move(self):
        result = {
            'name': _("Journal Entry Columbarium"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('sale_columnbarium_id','=',self.id)],
            'context':{
                'default_move_type': 'entry',
                'create': False,
            },
        }
        return result

    def action_create_invoice_columnbarium(self):
        if not self.columbarium_ids:
            raise UserError("Tidak ada product columbarium yang perlu dibuat Invoice.")
        self._create_inv_columnbarium()
        
    def prepare_invoice_columnbarium_vals(self, inv_line, date):
        invoice_vals = {
            'ref': self.client_order_ref,
            'date':date,
            'invoice_date':date,
            'invoice_date_due':date,
            'move_type': 'out_invoice',
            'invoice_origin': self.name,
            'invoice_user_id': self.user_id.id,
            'narration': self.note,
            'partner_id': self.partner_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_id.id)).id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'payment_reference': self.reference,
            'invoice_payment_term_id': self.payment_term_id.id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'team_id': self.team_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_line_ids': inv_line,
            'auto_post': True,
        }

        return invoice_vals
    
    def prepare_move_columnbarium_vals(self, detail_move, date):
        move_vals = {
            'ref': self.client_order_ref,
            'date':date,
            'move_type': 'entry',
            'narration': self.note,
            'partner_id': self.partner_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'line_ids': detail_move,
            'sale_columnbarium_id': self.id,
            'auto_post': True,
        }

        return move_vals
    
    def _create_inv_columnbarium(self):
        categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')

        for line in filter(lambda x : x.display_type != 'line_section' and x.product_id.categ_id.id == categ_columbarium.id
                           and not x.sale_columnbarium_upgrade_id, self.order_line): 
            d0 = date(line.pickup_date.year, line.pickup_date.month, line.pickup_date.day)
            d1 = date(line.return_date.year, line.return_date.month, line.return_date.day) + relativedelta(days=1)
            
            # diff = relativedelta(d1, d0)
            # periode_rental = (diff.years * 12) + diff.months
            # amount_column = line.price_subtotal / periode_rental

            # print("Days = ", (d1-d0).days)
            periode_rental = (d1-d0).days
            amount_column = line.price_subtotal / periode_rental

            multi_vals_inv = []
            multi_vals_entry = []

            # i = line.qty_invoiced 
            for i in range(int(line.qty_invoiced), int(periode_rental)):
                # print("invoice ke = ", i)
                detail_inv = []
                detail_inv.append([0,False,{
                    'name': line.product_id.name,
                    'price_unit': amount_column,
                    'quantity': 1.0,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'sale_line_ids': [(6, 0, [line.id])],
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'analytic_account_id': self.analytic_account_id.id or False,
                }])

                date_tmp = line.pickup_date + relativedelta(days=i)
                # res = calendar.monthrange(date_tmp.year, date_tmp.month)
                # day = res[1]
                # date_tmp = date(date_tmp.year, date_tmp.month, day)

                invoice_vals = self.prepare_invoice_columnbarium_vals(detail_inv, date_tmp)
                multi_vals_inv.append(invoice_vals)
                # invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)

                #
                detail_move = []
                detail_move.append([0, False, {
                    'account_id': self.payment_id.payment_line_ids[0].account_id.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.pricelist_id.currency_id.id,
                    'debit': amount_column,
                    'credit': 0,
                    'date_maturity': date_tmp,
                }])
                detail_move.append([0, False, {
                    'account_id': self.partner_id.property_account_receivable_id.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.pricelist_id.currency_id.id,
                    'debit': 0,
                    'credit': amount_column,
                    'date_maturity': date_tmp,
                }])
                move_vals = self.prepare_move_columnbarium_vals(detail_move, date_tmp)
                multi_vals_entry.append(move_vals)
                # move = self.env['account.move'].sudo().create(move_vals).with_user(self.env.uid)

        invoice = self.env['account.move'].sudo().create(multi_vals_inv).with_user(self.env.uid)
        move = self.env['account.move'].sudo().create(multi_vals_entry).with_user(self.env.uid)
        return self.action_view_invoice()
    
    # Auto Reconcile Rencananya mah
    def action_recon_hutang_titipo(self):
        for rec in self:
            if rec.payment_id: # ini menandakan bahwa sdh ada pembayaran kolombarium
                tgl_now = date(datetime.now().year, datetime.now().month, datetime.now().day)
                # tgl_now = date(year=2024, month=1, day=31)
                payment_move = self.env['account.move'].search([('payment_id','=',rec.payment_id.id)], limit=1)
                colum_move = self.env['account.move'].search([('sale_columnbarium_id','=',rec.id),('move_type','=','entry'),('date','=',tgl_now)], limit=1)
                recon_data_titipan = (payment_move + colum_move).line_ids.filtered(lambda x: x.account_id.id == rec.payment_id.payment_line_ids[0].account_id.id \
                                                                                   and (x.matching_number == 'P' or x.matching_number == '' or x.matching_number == False) \
                                                                                    and x.reconciled == False) 
                recon_data_titipan.reconcile()

                # ar invoice pada journal columbarium ar
                # self.partner_id.property_account_receivable_id.id
                inv_move = self.env['account.move'].search([('so_id','=',rec.id),('move_type','=','out_invoice'),('date','=',tgl_now)], limit=1)
                recon_data_ar = (inv_move + colum_move).line_ids.filtered(lambda x: x.account_id.id == rec.partner_id.property_account_receivable_id.id \
                                                                          and (x.matching_number == 'P' or x.matching_number == '' or x.matching_number == False) \
                                                                            and x.reconciled == False)
                recon_data_ar.reconcile()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # keperluan columbarium
    sale_columnbarium_upgrade_id = fields.Many2one('sale.order', string='Sales Order Upgrade Columbarium', readonly=True, store=True)
    is_notif_whatsapp = fields.Boolean(default=False)
    
    # def _prepare_invoice_line(self, **optional_values):
    #     res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
    #     categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
    #     if self.product_id.categ_id.id != categ_columbarium.id:
    #         return res
    #     else:
    #         return {}
        
    # button upgrade columnarium
    # def button_upgrade_columbarium(self):
    #     if not self.order_id.payment_id:
    #         raise UserError("Tidak bisa melakukan Upgrade Columbarium, \nSilakan lalukan penggantian Product Columbarium atau melakukan Pembayaran Columbarium agar dapat melakukan upgrade.")

    #     result = {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Upgrade Columbarium'),
    #         'res_model': 'upgrade.columbarium.wizard',
    #         'target': 'new',
    #         'view_id': self.env.ref('custom_accounting.upgrade_columbarium_wizard_view_form').id,
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'context': {
    #             'default_sale_order_id':self.order_id.id,
    #             'default_product_columbarium_id':self.product_id.id,
    #             'default_pickup_date':datetime.now(),
    #             'default_return_date':self.return_date,
    #             'default_list_price_original':self.price_unit,
    #             'default_sale_order_line_id': self.id,
    #         }
    #     }
    #     return result
    
    def unlink(self):
        for record in self:
            # kalau yang di delete merupakan columbarium upgrade
            if record.columbarium_upgrade_parent_id:
                record.columbarium_upgrade_parent_id.is_columbarium_upgraded = False

        return super(SaleOrderLine, self).unlink()

    is_columbarium_upgraded = fields.Boolean('Is Columbarium Upgraded?')
    columbarium_upgrade_parent_id = fields.Many2one('sale.order.line', string='Columbarium Upgrade Parent')

    def button_upgrade_columbarium(self):
        for record in self:
            # record.validate_change_pack_ruang_semayam()

            result = {
                'name': _('Upgrade Columbarium'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('custom_sale_order.change_product_wizard_view').id, 
                'res_model': 'change.product.wizard', 
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'upgrade_columbarium':True,
                    # 'default_current_price_unit':record.price_subtotal,
                    'default_so_id': record.order_id.id,
                    'default_so_line_id': record.id,
                    'default_pickup_date_new': record.pickup_date if record.pickup_date else None,
                    'default_return_date_new': record.return_date if record.return_date else None,
                    # 'default_pickup_date_new': datetime.now().date() + timedelta(days=1),
                    # 'default_return_date_new': datetime.now().date() + relativedelta(years=1),
                }
            }
            return result
    # button to sale upgrade
    # def button_to_sale_upgrade(self):
    #     result = {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Sale Order'),
    #         'res_model': 'sale.order',
    #         'target': 'current',
    #         'view_id': self.env.ref('sale_renting.rental_order_primary_form_view').id,
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'res_id': self.sale_columnbarium_upgrade_id.id,
    #     }
    #     return result
