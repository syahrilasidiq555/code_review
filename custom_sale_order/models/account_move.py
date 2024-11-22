# from attr import field
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime, timedelta
import json

class AccountMove(models.Model):
    _inherit = "account.move"

    # ADD PO, SO, COST SHEET FIELD if exist
    po_id = fields.Many2one('purchase.order', string='Purchase Order', compute="_compute_cs_po_so", store=True)
    so_id = fields.Many2one('sale.order', string='Sale Order', compute="_compute_cs_po_so", store=True)
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet', compute="_compute_cs_po_so", store=True)
    
    is_konsinyasi_bill = fields.Boolean('Is konsinyasi Bill?', readonly=True)

    invoice_user_id = fields.Many2one(string='Manager Penjual')
    employee_id = fields.Many2one(related="so_id.employee_id", store=True, readonly=False)

    penanggungjawab_id = fields.Many2one(related="so_id.penanggungjawab_id", string='Penanggung Jawab', store=True)
    penanggungjawab2_id = fields.Many2one(related="so_id.penanggungjawab2_id", string='Penanggung Jawab 2', store=True)

    @api.depends('invoice_origin')
    def _compute_cs_po_so(self):
        for record in self:
            record.po_id = None
            record.so_id = None
            record.cost_sheet_id = None
            
            if record.invoice_origin:
                # cari PO & SO
                purchase_order = self.env['purchase.order'].search([('name','=',record.invoice_origin)], limit=1)
                sale_order = self.env['sale.order'].search([('name','=',record.invoice_origin)], limit=1)
                cost_sheet = self.env['cost.sheet'].search([('name','=',record.invoice_origin)], limit=1)

                if purchase_order:
                    record.po_id = purchase_order[0].id
                    record.cost_sheet_id = purchase_order[0].cost_sheet_id if purchase_order[0].cost_sheet_id else False
                    
                elif sale_order:
                    record.so_id = sale_order[0].id
                    record.cost_sheet_id = sale_order[0].cost_sheet_id.id if sale_order[0].cost_sheet_id else False

                elif cost_sheet:
                    record.cost_sheet_id = cost_sheet[0].id
                    

    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 
    # @api.model_create_multi
    def create(self, values):
        res = super(AccountMove, self).create(values)
        # otomatis set invoice & billnya jadi posted
        # if res.so_id or res.po_id or res.is_konsinyasi_bill:
        #     if not res.invoice_date:
        #         res.invoice_date = datetime.now().date()

        #     if res.l10n_id_need_kode_transaksi:
        #         res.l10n_id_kode_transaksi = '01'

        #     res.sudo().action_post()
        for record in res:
            # produk child paket akunnya mengikuti parent paket
            for line in record.line_ids.filtered(lambda x: x.sale_line_ids):
                if line.sale_line_ids[0].parent_id:
                    paket_move_line_id = record.line_ids.filtered(lambda x: line.sale_line_ids[0].parent_id.id in x.sale_line_ids.ids)
                    if paket_move_line_id:
                        line.account_id = paket_move_line_id.account_id.id

            # kalau produknya columbarium maka ganti akunnya ke akun titipan columbarium
            categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            for line in record.line_ids.filtered(lambda x:x.product_id.product_tmpl_id.categ_id.id == categ_columbarium.id):
                if line.product_id.account_penangguhan_id:
                    line.account_id = line.product_id.account_penangguhan_id.id

        return res

    # # BUTTON CONFIRM
    def action_post(self):
        res = super(AccountMove, self).action_post()

        # create penangguhan pendapatan
        for record in self:
            categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            if record.so_id and record.move_type == 'out_invoice':
                for line in record.line_ids.filtered(lambda x:x.product_id.product_tmpl_id.categ_id.id == categ_columbarium.id and x.product_id.product_tmpl_id.pendapatan_asset_model_id):
                    # get asset_ids dari columbarium sebelumnya
                    if line.sale_line_ids[0].columbarium_upgrade_parent_id and line.sale_line_ids[0].columbarium_upgrade_parent_id.invoice_lines:
                        asset_id = line.sale_line_ids[0].columbarium_upgrade_parent_id.invoice_lines.move_id.asset_ids.filtered(lambda x: line.sale_line_ids[0].columbarium_upgrade_parent_id.invoice_lines[0].id in x.original_move_line_ids.ids )
                        if asset_id:
                            # first_depreciation_date = asset_id.first_depreciation_date
                            asset_id.original_move_line_ids = [(4,line.id)]
                            asset_id.sudo().write({
                                'first_depreciation_date': (line.sale_line_ids[0].pickup_date + timedelta(hours=7)).date(),
                                'columbarium_update_date': (line.sale_line_ids[0].pickup_date + timedelta(hours=7)).date()
                            })
                            # modify asset
                            total_days = 1+(line.sale_line_ids[0].return_date.date() - line.sale_line_ids[0].pickup_date.date()).days
                            # posted_depreciation_move_ids = asset_id.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
                            # columbarium_day_used = len(posted_depreciation_move_ids)

                            method_number = total_days
                            asset_modify_wizard = self.env['asset.modify'].create({
                                'asset_id': asset_id.id,
                                'name' : 'Columbarium Upgrade',
                                'method_period':'-1',
                                'method_number':method_number,
                            })
                            asset_modify_wizard.modify()
                            # raise UserError(str(asset_modify_wizard.read()))

                    # cek apakah sudah terbentuk atau belum
                    exist = False
                    if record.asset_ids and record.asset_ids.original_move_line_ids.filtered(lambda x: x.move_id.id == line.move_id.id):
                        exist = True

                    if not exist:
                        vals = {
                            'is_pengakuan_columbarium':True,
                            'asset_type':'sale',
                            'state':'draft',
                            'name':line.name,
                            'code_name':"PPC",
                            'acquisition_date':(line.sale_line_ids[0].pickup_date + timedelta(hours=7)).date(),
                            'first_depreciation_date':(line.sale_line_ids[0].pickup_date + timedelta(hours=7)).date(),
                            'model_id': line.product_id.product_tmpl_id.pendapatan_asset_model_id.id if line.product_id.product_tmpl_id.pendapatan_asset_model_id else None,
                            'account_depreciation_id': line.product_id.product_tmpl_id.pendapatan_asset_model_id.account_depreciation_id.id if line.product_id.product_tmpl_id.pendapatan_asset_model_id else None,
                            'account_depreciation_expense_id': line.product_id.product_tmpl_id.pendapatan_asset_model_id.account_depreciation_expense_id.id if line.product_id.product_tmpl_id.pendapatan_asset_model_id else None,
                            'journal_id': line.product_id.product_tmpl_id.pendapatan_asset_model_id.journal_id.id if line.product_id.product_tmpl_id.pendapatan_asset_model_id else None,
                            'original_move_line_ids':[(4,line.id)],
                            'method_number':1+(line.sale_line_ids[0].return_date - line.sale_line_ids[0].pickup_date).days, # ganti sama total hari rental columbarium
                            'method_period':'-1', # ganti sama hari
                        }
                        # data akan otomatis masuk ke field asset_ids
                        penangguhan_pendapatan = self.env['account.asset'].create(vals)
                        penangguhan_pendapatan.compute_depreciation_board()
                        # penangguhan_pendapatan.validate()
                        penangguhan_pendapatan.with_context(auto_post=True, validate=True, valid_state='draft').action_check()


    # # BUTTON DRAFT
    # def button_draft(self):
    #     res = super(AccountMove, self).button_draft()
        
    #     for record in self:
    #         # rollback rolling vendor
    #         record.roll_vendor_product_list_rollback()


    ###############################################################
    ##   METHOD
    ############################################################### 
    # roll vendor pada tiap2 product
    # def roll_vendor_product_list(self):
    #     for record in self:
    #         for line in record.invoice_line_ids:
    #             if line.cost_sheet_line_id and line.cost_sheet_line_id.is_konsinyasi:
    #                 line.product_id.product_tmpl_id.roll_vendor(record.partner_id.id)

    # # rollback roll vendor pada tiap2 product
    # def roll_vendor_product_list_rollback(self):
    #     for record in self:
    #         for line in record.invoice_line_ids:
    #             if line.cost_sheet_line_id and line.cost_sheet_line_id.is_konsinyasi:
    #                 line.product_id.product_tmpl_id.roll_vendor_rollback(record.partner_id.id)

    def action_merge_invoice(self):
        # validasi status harus posted
        invoice_not_posted_ids = self.filtered(lambda x: x.state != 'posted')
        if invoice_not_posted_ids:
            message = "Anda harus confirm Invoice terlebih dahulu sebelum melakukan merge, berikut ini adalah invoice yang belum di confirm:\n\n"
            for x in invoice_not_posted_ids:
                message += "- {name} ({partner}), {symbol} {amount}\n".format(
                    name = x.name,
                    partner = x.partner_id.name,
                    symbol = x.currency_id.symbol,
                    amount = f'{x.amount_total_signed:,}' 

                )
            raise ValidationError(message)

        # validasi merge invoice semayam
        invoice_sale_id = self.filtered(lambda x : x.so_id).sorted(lambda y: y.id)[0]
        if not invoice_sale_id:
            raise ValidationError("Anda hanya bisa menggabungkan Invoice POS ke Invoice Sale/Semayam!")
        # elif invoice_sale_id and len(invoice_sale_id) > 1:
        #     message = "Anda tidak dapat menggabungkan 2 atau lebih Invoice Sale/Semayam!\n\n"
        #     for x in invoice_sale_id:
        #         message += "- {name} ({partner}), {symbol} {amount}\n".format(
        #             name = x.name,
        #             partner = x.partner_id.name,
        #             symbol = x.currency_id.symbol,
        #             amount = f'{x.amount_total_signed:,}' 
        #         )
        #     raise ValidationError(message)

        # validasi invoice pos yang sudah dibayar
        invoice_pos_ids = self.filtered(lambda x : not x.so_id)
        for invoice_pos in invoice_pos_ids:
            if invoice_pos.payment_state == 'paid':
                message = "Invoice ini tidak dapat digabung karena sudah dibayar sepenuhnya: \n\n{name}".format(
                    name = invoice_pos.name
                )
                raise ValidationError(message)

        # validasi partner yang berbeda
        partners = []
        for x in self:
            if x.partner_id.id not in partners:
                partners.append(x.partner_id.id)
        if len(partners) > 1:
            raise ValidationError("Hanya dapat menggabungkan Invoice pada Almarhum yang sama!")

        # raise UserError(str(invoice_sale_id.invoice_line_ids))

        # ambil id register payment yang telah dilakukan
        registered_payment_ids = []
        if invoice_sale_id.invoice_payments_widget and json.loads(invoice_sale_id.invoice_payments_widget) and json.loads(invoice_sale_id.invoice_payments_widget).get('content'):
            for content in json.loads(invoice_sale_id.invoice_payments_widget).get('content'):
                registered_payment_ids.append(content)

        invoice_sale_id.button_draft()

        # for record in self.filtered(lambda x : not x.so_id):
        for record in self.filtered(lambda x : x.id != invoice_sale_id.id):
            # ambil id register payment yang telah dilakukan di invoice pos
            if record.invoice_payments_widget and json.loads(record.invoice_payments_widget) and json.loads(record.invoice_payments_widget).get('content'):
                for content in json.loads(record.invoice_payments_widget).get('content'):
                    registered_payment_ids.append(content)

            record.with_context(force_delete=True).button_draft()
            for line in record.invoice_line_ids:
                name = "{name} (POS : {ref})".format(
                    name = line.name,
                    ref = record.ref
                )
                invoice_sale_id.invoice_line_ids = [(0,0,{
                    'product_id':line.product_id.id,
                    'name': name,
                    'account_id':line.account_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': [(4,x) for x in line.tax_ids.ids],
                })]

                # tampilkan log produk apa saja yang di merge beserta dengan invoicenya
                invoice_sale_id.message_post(body="<b style='color:red;'>Item POS yang ditambahkan</b> : <br/><br/>Product : {product_name}<br/>Desc : {desc}<br/>Unit : {unit}<br/>Price: {price}".format(
                    product_name = line.product_id.name,
                    desc = name,
                    unit = line.quantity,
                    price = str(line.currency_id.symbol)+" "+ f"{line.price_unit:,}"
                ))
                
            pos_id = self.env['pos.order'].search([('name','=',record.ref)])
            if pos_id:
                pos_id.with_context(force_delete=True).account_move = invoice_sale_id.id

            # record.with_context(force_delete=True).button_draft()
            record.with_context(force_delete=True).name = None
            record.with_context(force_delete=True).unlink()

        invoice_sale_id.action_post()
        # reconcile yang sudah diregister payment sebelumnya
        if registered_payment_ids:
            for registered_payment_id in registered_payment_ids:
                invoice_sale_id.js_assign_outstanding_line(registered_payment_id['payment_id'])

        if invoice_sale_id:
            result = {
                    'name': 'Invoice',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    # 'view_type': 'form',
                    # 'views': [(form_view_id, 'form')],
                    'res_id': invoice_sale_id.id,
                    'context': {'create': False},
                }
            return result  

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cost_sheet_line_id = fields.Many2one('cost.sheet.line', string='Cost Sheet Line')
