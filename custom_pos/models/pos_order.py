from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

from functools import partial

from datetime import datetime, timedelta,date
import json

class PosOrder(models.Model):
    _inherit = 'pos.order'

    bill_ids = fields.Many2many(
        comodel_name="account.move", 
        relation="pos_bill_relation",
        column1="pos_order_id", 
        column2="move_id", 
        string="Bills List")
    
    # is_konsinyasi_retur = fields.Char(compute='_compute_is_konsinyasi_retur', string='Is KOnsinyasi Retur')
    
    # @api.depends('lines','lines.product_id','lines.product_id.is_konsinyasi','picking_ids')
    # def _compute_is_konsinyasi_retur(self):
    #     for record in self:
    #         if record.picking_ids:
    #             raise ValidationError(str(record.picking_ids))

    ###############################################################
    ##   INHERITED METHOD
    ###############################################################

    @api.model
    def create(self, values):
        res = super(PosOrder,self).create(values)
        res._set_employee_id()
        res.create_konsinyasi_bill()
        if res.refunded_order_ids:
            res.remove_or_recreate_konsinyasi_bills()
        return res
    
    # set employee field
    def _set_employee_id(self):
        for record in self:
            if self.env.user.employee_id:
                record.sudo().employee_id = self.env.user.employee_id.id

    # set field kode transaksi untuk partner dengan id pkp
    def _prepare_invoice_vals(self):
        vals = super(PosOrder,self)._prepare_invoice_vals()
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner and partner.l10n_id_pkp:
                vals['l10n_id_kode_transaksi'] = '01'

        return vals

    # set field penanggung jawab pada saat create invoice, jika ada fieldnya
    def _generate_pos_order_invoice(self):
        res = super(PosOrder,self)._generate_pos_order_invoice()
        for record in self:
            if record.penanggungjawab_id:
                record.account_move.penanggungjawab_id = record.penanggungjawab_id

            # check kalau invoicenya REFUND / RETUR maka otomatis reconcile
            if record.refunded_order_ids and record.account_move.reversed_entry_id and record.account_move.invoice_outstanding_credits_debits_widget and json.loads(record.account_move.invoice_outstanding_credits_debits_widget) and json.loads(record.account_move.invoice_outstanding_credits_debits_widget).get('content'):
                # refunded_order_ids_name = [x.name for x in record.refunded_order_ids]
                refunded_order_ids_move_ids = [x.account_move.id for x in record.refunded_order_ids.filtered(lambda x: x.account_move)]
                for content in json.loads(record.account_move.invoice_outstanding_credits_debits_widget).get('content'):
                    if content['move_id'] in refunded_order_ids_move_ids:
                        record.account_move.js_assign_outstanding_line(content['id'])


    # kalau payment methodnya bayar nanti maka otomatis create faktur
    @api.model
    def _order_fields(self, ui_order):
        fields = super(PosOrder, self)._order_fields(ui_order)

        try:
            pay_later_id = self.env.ref('custom_pos.pos_payment_paylater').id
        except:
            pay_later_id = 0
        auto_to_invoice = False
        for payment in ui_order['statement_ids']:
            auto_to_invoice = True if payment[2]['payment_method_id'] == pay_later_id else auto_to_invoice
            break

        to_invoice = ui_order['to_invoice'] if "to_invoice" in ui_order else False
        if auto_to_invoice and ui_order.get('partner_id'):
            to_invoice = True

        fields.update({
            'to_invoice': to_invoice,
        })

        return fields

    ###############################################################
    ##   METHOD
    ############################################################### 

    # tombol view bills
    def action_view_bills(self):
        result = {
            'name': _("Vendor Bills"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_in_invoice_bill_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form')
            ],
            'domain': [('id', 'in', self.bill_ids.ids)],
            'context': {
                'create': False,
                'default_move_type': 'in_invoice'
            }
        }
        return result

    penanggungjawab_id = fields.Many2one('res.partner', string='Penanggung Jawab', tracking=True, 
        domain="['|', '&', '&',('company_id', '=', False), ('company_id', '=', company_id), ('is_penanggungjawab', '=', True), ('parent_id', '=', partner_id)]")    
    is_paylater_semayam = fields.Boolean(compute='_compute_is_paylater_semayam', string='Is Paylater Semayam', store=True)
    @api.depends('payment_ids','partner_id')
    def _compute_is_paylater_semayam(self):
        for record in self: 
            is_paylater_semayam = False

            try:
                pay_later_id = self.env.ref('custom_pos.pos_payment_paylater')
            except:
                pay_later_id = self.env[self._name].search([],limit=1)
        
            if record.payment_ids.filtered(lambda x: x.payment_method_id.id == pay_later_id.id):
                is_paylater_semayam = True
                
                if record.partner_id.is_penanggungjawab:
                    record.penanggungjawab_id = record.partner_id
                    record.partner_id = record.partner_id.parent_id
                elif record.partner_id.is_jenazah and record.partner_id.child_ids:
                    record.penanggungjawab_id = record.partner_id.child_ids[0].id

            record.is_paylater_semayam = is_paylater_semayam
            

    def create_konsinyasi_bill(self,registered_payment_ids=[]):
        for record in self:
            # CREATE KONSINYASI BILLS
            bill_ids = []

            # get vendor list
            vendor_list = []
            for line in record.lines.filtered(lambda x : x.product_id.is_konsinyasi and x.product_id.seller_ids and not x.refunded_orderline_id and (x.qty - x.refunded_qty) != 0):
                vendor_list.append(line.product_id.seller_ids[0].name.id)

            for vendor_id in vendor_list:
                invoice_line_ids = []
                # get product konsinyasi dan bukan produk refund
                for line in record.lines.filtered(lambda x : x.product_id.is_konsinyasi and not x.refunded_orderline_id and (line.qty - line.refunded_qty) != 0):
                    if line.product_id.seller_ids[0].name.id == vendor_id:
                        invoice_line_ids.append((0,0,{
                            # 'cost_sheet_line_id':line.id,
                            'pos_line_id':line.id,
                            'product_id':line.product_id.id,
                            'name': line.full_product_name,
                            'quantity': (line.qty - line.refunded_qty) if line.refunded_qty else line.qty,
                            'price_unit': line.product_id.seller_ids[0].price if line.product_id.seller_ids else 0
                        }))
                
                values = {
                    'move_type': 'in_invoice',
                    'is_konsinyasi_bill': True,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    'date': record.date_order,
                    'invoice_date': record.	date_order,
                    'partner_id': vendor_id,
                    'invoice_origin':record.name,
                    'invoice_line_ids': invoice_line_ids
                }
                bill = self.env['account.move'].create(values)

                if registered_payment_ids:
                    pass
                    # bill.action_post()
                    # for registered_payment_id in registered_payment_ids:
                    #     bill.js_assign_outstanding_line(registered_payment_id['payment_id'])

                bill_ids.append((4, bill.id))

            if bill_ids:
                record.bill_ids = bill_ids
    
    # REMOVE KONSINYASI BILLS (kalau POS ini ada retur)
    # delete bills konsinyasi yang lama, kalau ada yang di retur
    # buat ulang konsinyasi billsnya (qty = qty - refunded qty)
    # register payment otomatis (jika ada)
    def remove_or_recreate_konsinyasi_bills(self):
        for record in self:
            if record.refunded_order_ids:
                for refunded_order in record.refunded_order_ids.filtered(lambda x: x.bill_ids):
                    # delete konsinyasi bills

                    for bill in refunded_order.bill_ids:
                        # cek apakah sudah posted
                        registered_payment_ids = []
                        if bill.state == 'posted':
                            if bill.invoice_payments_widget and json.loads(bill.invoice_payments_widget) and json.loads(bill.invoice_payments_widget).get('content'):
                                for content in json.loads(bill.invoice_payments_widget).get('content'):
                                    registered_payment_ids.append(content)

                            bill.with_context(force_delete=True).button_draft()
                            bill.with_context(force_delete=True).name = None
                        bill.with_context(force_delete=True).unlink()
                        
                        # create ulang konsinyasi billsnya
                        refunded_order.create_konsinyasi_bill(registered_payment_ids=registered_payment_ids)

