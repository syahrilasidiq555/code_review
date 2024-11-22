from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, format_datetime, format_time
from collections import defaultdict

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta 

import json

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet')
    deleted_order_line = fields.One2many('sale.order.line.deleted', 'order_id', string='Produk Paket yang di delete')

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', '&', ('company_id', '=', False), ('company_id', '=', company_id), ('is_jenazah','=', True)]",
        String="Almarhum")
        
    almarhum_usia = fields.Integer(related="partner_id.usia")

    tanggal_keluar = fields.Datetime('Tanggal Keluar')

    # jenazah_id = fields.Many2one('res.partner', string='Jenazah', tracking=True, 
    #     domain="['|', '&', '&',('company_id', '=', False), ('company_id', '=', company_id), ('is_jenazah', '=', True), ('parent_id', '=', partner_id)]")

    penanggungjawab_id = fields.Many2one('res.partner', string='Penanggung Jawab', tracking=True, 
        domain="['|', '&', '&',('company_id', '=', False), ('company_id', '=', company_id), ('is_jenazah', '!=', True), ('parent_id', '=', partner_id)]")    

    penanggungjawab2_id = fields.Many2one('res.partner', string='Penanggung Jawab 2', tracking=True, 
        domain="['|', '&', '&',('company_id', '=', False), ('company_id', '=', company_id), ('is_jenazah', '!=', True), ('parent_id', '=', partner_id)]")    


    user_id = fields.Many2one(string='Manager Penjual')
    employee_id = fields.Many2one('hr.employee', string='Penjual')

    voucher_parkir_ids = fields.One2many('parking.voucher', 'sale_order_id', string='Voucher Parkir')

    # informasi tambahan
    almarhum_jenis_kelamin = fields.Selection(related="partner_id.jenis_kelamin", readonly=False)
    almarhum_agama = fields.Selection(related="partner_id.agama", readonly=False)
    almarhum_usia = fields.Integer(related="partner_id.usia", readonly=False)
    almarhum_penyakit = fields.Char(related="partner_id.penyakit", readonly=False)
    almarhum_tanggal_kedatangan = fields.Datetime(related="partner_id.tanggal_kedatangan", readonly=False)
    almarhum_asal = fields.Char(related="partner_id.asal", readonly=False)
    almarhum_pelayanan = fields.Char(related="partner_id.pelayanan", readonly=False)
    almarhum_no_pol_kendaraan = fields.Char(related="partner_id.no_pol_kendaraan", readonly=False)
    almarhum_ruangan_id = fields.Many2one(related="partner_id.ruangan_id", readonly=False)
    almarhum_paket_id = fields.Many2one(related="partner_id.paket_id", readonly=False)
    almarhum_peti_id = fields.Many2one(related="partner_id.peti_id", readonly=False)
    # almarhum_is_transit = fields.Boolean(related="partner_id.is_transit", readonly=False)
    almarhum_tanggal_terima_abu = fields.Datetime(related="partner_id.tanggal_terima_abu", readonly=False)
    almarhum_jadwal_ibadah = fields.Datetime(related="partner_id.jadwal_ibadah", readonly=False)
    almarhum_nama_pemuka_agama = fields.Char(related="partner_id.nama_pemuka_agama", readonly=False)
    almarhum_paroki = fields.Char(related="partner_id.paroki", readonly=False)
    almarhum_tanggal_keberangkatan = fields.Datetime(related="partner_id.tanggal_keberangkatan", readonly=False)
    almarhum_keterangan = fields.Text(related="partner_id.keterangan", readonly=False)


    paket_id = fields.Many2one('product.template', compute='_compute_paket_id', string='Paket', store=True)
    @api.depends('order_line','order_line.product_id','order_line.paket_id')
    def _compute_paket_id(self):
        for record in self:
            paket_id = None
            if record.order_line:
                lines = record.order_line.filtered(lambda x: x.paket_id)
                for line in lines:
                    paket_id = line.paket_id
                    break
            record.paket_id = paket_id

    ruang_semayam_id = fields.Many2one('product.product',compute='_compute_ruang_semayam_id', string='Ruang Semayam', store=True)
    ruang_semayam_order_line_id = fields.Many2one('sale.order.line',compute='_compute_ruang_semayam_id', string='Line Ruang Semayam', store=True)
    @api.depends('order_line','order_line.product_id','order_line.paket_id','order_line.is_ruang_semayam','order_line.is_from_ruang_semayam_wizard')
    def _compute_ruang_semayam_id(self):
        for record in self:
            ruang_semayam_id = None
            ruang_semayam_order_line_id = None
            if record.order_line:
                # lines = record.order_line.filtered(lambda x: x.paket_id and x.is_ruang_semayam)
                lines = record.order_line.filtered(lambda x: x.is_ruang_semayam)
                for line in lines:
                    ruang_semayam_order_line_id = line.id
                    # ruang_semayam_id = line.product_id if not line.pengganti_id else line.pengganti_id.product_id
                    ruang_semayam_id = line.pengganti_id.product_id if line.pengganti_id and line.pengganti_id.id != line.parent_id.id else line.product_id
                    break
            record.ruang_semayam_id = ruang_semayam_id
            record.ruang_semayam_order_line_id = ruang_semayam_order_line_id
    
    check_out_ruang_semayam_visible = fields.Boolean(compute='_compute_check_out_ruang_semayam_visible', string='CheckOut Ruang Semayam Visible')
    
    @api.depends('ruang_semayam_id','ruang_semayam_order_line_id','ruang_semayam_order_line_id.qty_delivered','ruang_semayam_order_line_id.qty_returned')
    def _compute_check_out_ruang_semayam_visible(self):
        for record in self:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            record.check_out_ruang_semayam_visible = False
            if record.ruang_semayam_id and record.ruang_semayam_order_line_id:
                if record.ruang_semayam_order_line_id.state in ['sale', 'done'] and record.ruang_semayam_order_line_id.is_rental and record.ruang_semayam_order_line_id.qty_delivered > 0 and record.ruang_semayam_order_line_id.qty_returned < 1:
                    record.check_out_ruang_semayam_visible = True
                    

    columbarium_ids = fields.Many2many(
        comodel_name="product.product", 
        relation="sale_order_columbarium_relation",
        column1="sale_order_id", 
        column2="product_id", 
        string='Columbarium',compute='_compute_columbarium_ids', store=True)
    columbarium_start = fields.Datetime(string='Columbarium Start', compute='_compute_columbarium_ids', store=True)
    columbarium_end = fields.Datetime(string='Columbarium end', compute='_compute_columbarium_ids', store=True)
    
    @api.depends('order_line','order_line.product_id','order_line.paket_id','order_line.is_columbarium')
    def _compute_columbarium_ids(self):
        for record in self:
            columbarium_ids = []
            columbarium_start = False
            columbarium_end = False
            if record.order_line:
                # lines = record.order_line.filtered(lambda x: x.paket_id and x.is_ruang_semayam)
                lines = record.order_line.filtered(lambda x: x.is_columbarium and not x.pengganti_id)
                columbarium_ids.append((5,0))
                for line in lines:
                    columbarium_ids.append((4,line.product_id.id))
                    if not columbarium_start and not columbarium_end:
                        columbarium_start = line.pickup_date
                        columbarium_end = line.return_date     
                    columbarium_start = line.pickup_date if columbarium_start and columbarium_start > line.pickup_date else columbarium_start
                    columbarium_end = line.return_date if columbarium_end and columbarium_end < line.return_date else columbarium_end
            record.columbarium_ids = columbarium_ids
            record.columbarium_start = columbarium_start
            record.columbarium_end = columbarium_end

    ###############################################################
    ##   INHERITED METHOD
    ############################################################### 
    # BUTTON CONFIRM
    def action_confirm(self):
        for record in self:
            # validasi
            is_less_product = False
            message = "Berikut ini adalah beberapa data produk yang memiliki qty di inventory yang tidak cukup : \n\n"

            # get minus product
            ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            for index,line in enumerate(record.order_line.filtered(lambda x: x.product_uom_qty > 0 and x.product_id.detailed_type not in ['consu','service'] and  x.free_qty < x.product_uom_qty and x.product_id.categ_id.id != ruang_semayam_category_id.id), 1):
                is_less_product = True
                message += "{index}. {name}\nQty : {product_uom_qty}, Qty Free : {free_qty} \n\n".format(
                    index = index,
                    name = line.name,
                    product_uom_qty = line.product_uom_qty,
                    free_qty = line.free_qty
                )

            okey = self._context.get('okey',False)
            if is_less_product and not okey:
                context = {
                    'default_message': message,
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_confirm",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Warning',
                    'res_model':'confirm.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_view_3').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
            
        res = super(SaleOrder, self).action_confirm()

        # BUAT COST SHEET BERDASARKAN SALES INI
        for record in self:
            if not record.cost_sheet_id:
                record.action_create_cost_sheet()
                record.cost_sheet_id.state = 'approved'
                record.cost_sheet_id.action_create_po_and_bills()
                # record.auto_occupy_ruang_semayam()
                # # confirm all PO
                # for po in record.cost_sheet_id.po_ids:
                #     po.button_confirm()
    
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for record in self:
            record.action_create_new_cost_sheet_line()
        return res

    # @api.constrains('jenazah_id')
    # def _constrains_jenazah_id(self):
    #     for rec in self:
    #         if rec.jenazah_id and rec.jenazah_id.parent_id.id != rec.partner_id.id:
    #             # raise ValidationError("Jenazah is not connected to the partner that has been selected.")
    #             raise ValidationError("Jenazah tidak tersambung ke partner yang dipilih.")


    ###############################################################
    ##   METHOD
    ############################################################### 
    
    # validasi ruang semayam yang tidak boleh di add pada paket tertentu
    # def validate_ruang_semayam(self):
    #     for record in self:
    #         ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
    #         # get paket
    #         paket_ids = record.order_line.filtered(lambda x: x.paket_id and not x.paket_id.pelebaran_ruangan)
    #         for paket_id in paket_ids:
    #             product_ruang_semayam_ids = record.order_line.filtered(lambda x: x.product_id.product_tmpl_id.categ_id.id == ruang_semayam_category_id.id and not x.parent_id)
    #             if product_ruang_semayam_ids:
    #                 message = "Paket yang dipilih ({paket_id}) tidak boleh ada tambahan item sebagai berikut: \n\n".format(
    #                     paket_id = paket_id.name
    #                 )
    #                 for index,product in enumerate(product_ruang_semayam_ids,1):
    #                     message += "{index}. {product_name}\n\n".format(
    #                         index = index,
    #                         product_name = product.name
    #                     )
    #                 raise ValidationError(message)
    
    # # Validasi Paket
    # @api.constrains('paket_id','order_line','order_line.product_id','order_line.paket_id')
    # def _constrains_paket_id(self):
    #     for record in self:
    #         paket_ids = record.order_line.filtered(lambda x: x.paket_id and x.paket_id.id != record.paket_id.id)
    #         if paket_ids and record.paket_id:
    #             message = "Anda sudah memilih paket {paket_name}, tidak boleh menambah paket lebih dari 1.\nJika ingin mengganti paket silahkan hapus item paket yang telah diisi sebelumnya!"
    #             raise UserError(message)


    def _validasi_tambah_ruang_semayam_baru(self):
        for record in self:
            if record.paket_id:
                raise ValidationError("Anda telah memilih paket sebelumnya, tidak boleh tambah ruang semayam yang baru!\n\nSilahkan pilih penambahan hari / lebar")
    
    def _validasi_tambah_hari_lebar_ruang_semayam(self):
        for record in self:
            # if not record.paket_id:
            #     raise ValidationError("Tidak boleh memilih tipe penambahan Hari / Lebar ruang semayam karena anda belum memilih paket sebelumnya!")
            if not record.ruang_semayam_id:
                raise ValidationError("Tidak boleh memilih tipe penambahan Hari / Lebar ruang semayam karena anda belum memilih ruang semayam!")
            if record.paket_id and not record.paket_id.pelebaran_ruangan:
                raise ValidationError("Paket ini tidak memperbolehkan untuk pelebaran ruangan, tidak boleh tambah ruang semayam yang baru!")
    

    # validasi tambah ruang semayam kalau dari add product
    @api.constrains('order_line','order_line.product_id','order_line.product_uom_qty','order_line.is_produk_pengganti')
    def _constrains_order_line(self):
        for record in self:
            ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            product_ruang_semayam_ids = record.order_line.filtered(lambda x: x.product_id.product_tmpl_id.categ_id.id == ruang_semayam_category_id.id and not x.parent_id and not x.is_from_ruang_semayam_wizard)
            if product_ruang_semayam_ids:
                message = "Untuk menambah ruang semayam gunakan tombol 'Tambah Ruang Semayam', sebelum melanjutkan silahkan klik batal atau hapus data berikut ini: \n\n"
                for index,product in enumerate(product_ruang_semayam_ids,1):
                    message += "{index}. {product_name}\n\n".format(
                        index = index,
                        product_name = product.name
                    )
                raise ValidationError(message)
            
    # validasi tambah transportasi jenazah dari add product
    @api.constrains('order_line','order_line.product_id','order_line.product_uom_qty','order_line.is_produk_pengganti')
    def _constrains_order_line(self):
        for record in self:
            transport_jenazah_category_id = self.env.ref('custom_sale_order.categ_transportasi_jenazah')
            product_transportasi_ids = record.order_line.filtered(lambda x: x.product_id.product_tmpl_id.categ_id.id == transport_jenazah_category_id.id and not x.parent_id and not x.is_from_transportasi_wizard and not x.is_produk_pengganti)
            if product_transportasi_ids:
                message = "Untuk menambah transportasi jenazah gunakan tombol 'Tambah Transportasi Jenazah', sebelum melanjutkan silahkan klik batal atau hapus data berikut ini: \n\n"
                for index,product in enumerate(product_transportasi_ids,1):
                    message += "{index}. {product_name}\n\n".format(
                        index = index,
                        product_name = product.name
                    )
                raise ValidationError(message)

    # action untuk create cost sheet
    def action_create_cost_sheet(self):
        for record in self:
            cost_sheet_line = []
            
            for item in record.order_line.filtered(lambda x : x.display_type != "line_section" and (x.product_id.detailed_type in ['consu','service'] or x.product_id.is_konsinyasi)):
                cost_sheet_line.append([0,0,{
                    'sale_order_line_id': item.id,
                    'product_id':item.product_id.id,
                    'name': item.name,
                    'budget_cost':0
                }])

            vals = {
                # 'partner_id': record.partner_id.id,
                'sale_order_id': record.id,
                'date': record.date_order,
                'cost_sheet_line':cost_sheet_line
            }        
            cost_sheet = self.env['cost.sheet'].create(vals)            
            record.cost_sheet_id = cost_sheet.id

    def action_create_new_cost_sheet_line(self):
        for record in self:
            if record.cost_sheet_id:
                if not record.cost_sheet_id.sale_order_id:
                    record.cost_sheet_id.sale_order_id = record.id

                cost_sheet_line = []
            
                for item in record.order_line.filtered(lambda x : not x.cost_sheet_line_id and x.display_type != "line_section" and (x.product_id.detailed_type in ['consu','service'] or x.product_id.is_konsinyasi)):
                    cost_sheet_line.append([0,0,{
                        'sale_order_line_id': item.id,
                        'product_id':item.product_id.id,
                        'name': item.name,
                        'budget_cost':0
                    }])

                if cost_sheet_line:
                    record.cost_sheet_id.cost_sheet_line = cost_sheet_line
                if not record.cost_sheet_id.is_all_po_bill_created:
                    record.cost_sheet_id.action_create_po_and_bills()

    # button view rental schedule
    def action_view_rental_schedule(self):
        for record in self:
            if record.is_rental_order:
                result = {
                    'name': _("Schedule of {so_name} ({cust_name})".format(
                        so_name = record.name,
                        cust_name = record.partner_id.name
                    )),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.rental.schedule',
                    'view_mode': 'tree,gantt',
                    # 'view_type': 'form',
                    'views': [
                        (self.env.ref('custom_sale_order.rental_schedule_view_tree').id, 'tree'),
                        (self.env.ref('sale_renting.rental_schedule_view_gantt').id, 'gantt')
                    ],
                    'domain': [('order_id','=',record.id)],
                    'context': {'create': False},
                }
                return result  
    
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

    # Button Add Pack
    def get_bundle_product_list(self):
        for record in self:
            if record.paket_id:
                raise ValidationError("Tidak boleh menambah paket lebih dari 1, silahkan hapus item paket yang telah diisi sebelumnya jika ingin mengganti paket!")
            
            result = {
                'type': 'ir.actions.act_window',
                'name': _('Product Pack'),
                'res_model': 'bundle.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.ni_bundle_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'tanggal_kedatangan':record.customer_form_id.almarhum_tanggal_kedatangan if record.customer_form_id else None
                }
            }
        return result

    # button tambah ruangan semayam
    def action_add_ruang_semayam(self):
        for record in self:
            result = {
                'type': 'ir.actions.act_window',
                'name': _('Tambah Ruang Semayam'),
                'res_model': 'add.ruang.semayam.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.add_ruang_semayam_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_sale_order_id':record.id,
                    'default_return_date_new': record.ruang_semayam_order_line_id.return_date.replace(hour=23, minute=59, second=59) + timedelta(days=1, hours=-7) if record.ruang_semayam_order_line_id and record.ruang_semayam_order_line_id.return_date else None,
                    'default_start_date_new_lebar': record.ruang_semayam_order_line_id.pickup_date if record.ruang_semayam_order_line_id and record.ruang_semayam_order_line_id.pickup_date else None,
                    'default_return_date_new_lebar': record.ruang_semayam_order_line_id.return_date if record.ruang_semayam_order_line_id and record.ruang_semayam_order_line_id.return_date else None,
                }
            }
            return result
    
    # button tambah transportasi
    def action_add_transportasi(self):
        for record in self:
            result = {
                'type': 'ir.actions.act_window',
                'name': _('Tambah Transportasi Jenazah'),
                'res_model': 'add.transportasi.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.add_transportasi_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_sale_order_id':record.id,
                }
            }
            return result
    
    # button tambah columbarium
    def action_add_columbarium(self):
        for record in self:
            # raise UserError("tambah columbarium")
            context = {
                'default_sale_order_id':record.id,
            }
            if record.partner_id.jadwal_kremasi:
                context['default_pickup_date'] = record.partner_id.jadwal_kremasi
                context['default_return_date'] = record.partner_id.jadwal_kremasi + timedelta(days=-1) + relativedelta(years=1)
            
            result = {
                'type': 'ir.actions.act_window',
                'name': _('Tambah Columbarium'),
                'res_model': 'add.columbarium.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.add_columbarium_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': context
            }
            return result
    
    # button tambah ruangdoa
    def action_add_ruangdoa(self):
        for record in self:
            # raise UserError("tambah ruangdoa")
            result = {
                'type': 'ir.actions.act_window',
                'name': _('Tambah Ruangdoa'),
                'res_model': 'add.ruangdoa.wizard',
                'target': 'new',
                'view_id': self.env.ref('custom_sale_order.add_ruangdoa_wizard_view_form').id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_sale_order_id':record.id,
                }
            }
            return result

    # button refresh qty
    def action_refresh_qty(self):
        for record in self:
            for line in record.order_line:
                line._compute_warehouse_qty()

    # inherit open return button
    def open_return(self):
        status = "return"
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lines_to_return = self.order_line.filtered(
            lambda r: r.state in ['sale', 'done'] and r.is_rental and float_compare(r.qty_delivered, r.qty_returned, precision_digits=precision) > 0 and r.is_ruang_semayam != True)
        return self._open_rental_wizard(status, lines_to_return.ids)

    # button checkout ruang semayam
    def ruang_semayam_co(self):
        for record in self:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines_to_return = self.order_line.filtered(
                lambda r: r.state in ['sale', 'done'] and r.is_rental and float_compare(r.qty_delivered, r.qty_returned, precision_digits=precision) > 0 and r.is_ruang_semayam == True)
            if record.ruang_semayam_order_line_id:
                return record._open_rental_wizard('return', lines_to_return.ids)
                # create rental wizard
                rental_wiz = self.env['rental.order.wizard'].sudo().with_context(order_line_ids=[record.ruang_semayam_order_line_id.id]).create({
                    'status': 'return',
                    'order_id': record.id
                })
                # raise UserError(str(rental_wiz.rental_wizard_line_ids.read()))
                rental_wiz.apply()

    
    def pickup_or_return_ruang_semayam(self,status):
        for record in self:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            ruang_semayam_list = None
            if status == 'pickup':
                ruang_semayam_list = record.order_line.filtered(
                    lambda r: r.state in ['sale', 'done'] and r.is_rental and float_compare(r.product_uom_qty, r.qty_delivered, precision_digits=precision) > 0 and r.is_ruang_semayam == True
                )
            elif status == 'return':
                ruang_semayam_list = self.order_line.filtered(
                    lambda r: r.state in ['sale', 'done'] and r.is_rental and float_compare(r.qty_delivered, r.qty_returned, precision_digits=precision) > 0 and r.is_ruang_semayam == True)

            if ruang_semayam_list:
                # raise UserError(str(ruang_semayam_list.read()))
                # status = 'pickup'
                rental_wizard_line_ids = []
                for rsemayam in ruang_semayam_list:
                    delay_price = rsemayam.product_id._compute_delay_price(fields.Datetime.now() - rsemayam.return_date)
                    rental_wizard_line_ids.append((0,0,{
                        'order_line_id': rsemayam.id,
                        'product_id': rsemayam.product_id.id,
                        'qty_reserved': rsemayam.product_uom_qty,
                        'qty_delivered': rsemayam.qty_delivered if status == 'return' else rsemayam.product_uom_qty - rsemayam.qty_delivered,
                        'qty_returned': rsemayam.qty_returned if status == 'pickup' else rsemayam.qty_delivered - rsemayam.qty_returned,
                        'is_late': rsemayam.is_late and delay_price > 0
                    }))
                rental_wiz = self.env['rental.order.wizard'].sudo().create({
                        'status': status,
                        'order_id': record.id,
                        'rental_wizard_line_ids':rental_wizard_line_ids,
                    })
                # raise UserError(str(rental_wiz.rental_wizard_line_ids.read()))
                rental_wiz.sudo().apply()
    
    def auto_pickup_ruang_semayam(self,order_lines):
        so_list = self.browse([line.order_id.id for line in order_lines])
        for so in so_list:
            so.pickup_or_return_ruang_semayam('pickup')
    
    def auto_return_ruang_semayam(self,order_lines):
        so_list = self.browse([line.order_id.id for line in order_lines])
        for so in so_list:
            so.pickup_or_return_ruang_semayam('return')

    # cron auto pickup and return ruang semayam sejuai jadwal
    def cron_pickup_return_ruang_semayam_as_schedule(self,date=datetime.now()):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # get order line to pickup as date
        # order_lines = self.env['sale.order.line'].search([
        #     ('is_rental','=',True),
        #     ('is_ruang_semayam','=',True),
        #     ('state','in',['sale','done']),
        #     '|',
        #     ('pickup_date','<=',date),
        #     ('return_date','<=',date),
        # ], order="id asc")
        # raise UserError(str(order_lines.read()))
        # raise UserError(str(order_lines.filtered(lambda r: float_compare(r.product_uom_qty, r.qty_delivered, precision_digits=precision) > 0 and 
        #     not (r.pickup_date < date and r.return_date < date)).read()))

        # auto pickup
        order_lines_pickup = self.env['sale.order.line'].search([
            ('is_rental','=',True),
            ('is_ruang_semayam','=',True),
            ('state','in',['sale','done']),
            ('pickup_date','<=',date),
            ('qty_delivered','=',0),
        ], order="id asc")
        self.auto_pickup_ruang_semayam(order_lines_pickup.filtered(lambda r: float_compare(r.product_uom_qty, r.qty_delivered, precision_digits=precision) > 0 and 
            not (r.pickup_date < date and r.return_date < date)))
        
        # auto return
        order_lines_return = self.env['sale.order.line'].search([
            ('is_rental','=',True),
            ('is_ruang_semayam','=',True),
            ('state','in',['sale','done']),
            ('return_date','<=',date),
            ('qty_returned','=',0),
        ], order="id asc")
        self.auto_return_ruang_semayam(order_lines_return.filtered(lambda r: float_compare(r.qty_delivered, r.qty_returned, precision_digits=precision) > 0))
        

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # default vendor
    default_vendor_id = fields.Many2one('res.partner', string='Default Vendor')    

    # inherit product_id unutk set domain
    product_id_domain = fields.Char(compute="_compute_product_id_domain", string="product id domain")

    @api.depends('order_id', 'order_id.company_id')
    def _compute_product_id_domain(self):
        for record in self:
            categ_ids = []
            categ_ruang_semayam = self.env.ref('custom_sale_order.categ_ruang_semayam')
            if categ_ruang_semayam:
                categ_ids.append(categ_ruang_semayam.id)
            
            categ_transportasi_jenazah = self.env.ref('custom_sale_order.categ_transportasi_jenazah')
            if categ_transportasi_jenazah:
                categ_ids.append(categ_transportasi_jenazah.id)
            
            categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            if categ_columbarium:
                categ_ids.append(categ_columbarium.id)
            
            categ_ruangdoa = self.env.ref('custom_sale_order.categ_ruangdoa')
            if categ_ruangdoa:
                categ_ids.append(categ_ruangdoa.id)

            domain = [
                ('categ_id','not in',categ_ids),
                '|', ('sale_ok', '=', True), ('rent_ok', '=', True), 
                '|', ('company_id', '=', False), ('company_id', '=', record.order_id.company_id.id)
            ]

            record.product_id_domain = json.dumps(domain)

    # product_id = fields.Many2one(domain=_get_product_id_domain)

    qty_returned = fields.Float(digits='Product Unit of Measure')

    qty_available = fields.Float(string='Qty di inventori', compute="_compute_warehouse_qty", store=True, digits='Product Unit of Measure')
    virtual_available = fields.Float(string='Qty Perkiraan', compute="_compute_warehouse_qty", store=True, digits='Product Unit of Measure')
    free_qty = fields.Float(string='Qty Free', compute="_compute_warehouse_qty", store=True, digits='Product Unit of Measure')

    @api.depends('product_id','product_warehouse_id')
    def _compute_warehouse_qty(self):
        for record in self:
            qty_available = 0
            virtual_available = 0
            free_qty = 0

            if record.product_id and record.product_warehouse_id:
                qty_available = record.product_id.with_context({'warehouse': record.product_warehouse_id.id}).qty_available
                virtual_available = record.product_id.with_context({'warehouse': record.product_warehouse_id.id}).virtual_available
                free_qty = record.product_id.with_context({'warehouse': record.product_warehouse_id.id}).free_qty

            record.qty_available = qty_available
            record.virtual_available = virtual_available
            record.free_qty = free_qty

    # hanya sebagai penanda
    paket_id = fields.Many2one('product.template', string='Paket', help="relasi ke paket di section")
    parent_id = fields.Many2one('sale.order.line', string='Paket', help="parent kalau dipilih melalui paket")

    pengganti_id = fields.Many2one('sale.order.line', string='Produk Pengganti')
    is_produk_pengganti = fields.Boolean('Is Produk Pengganti')

    is_from_transportasi_wizard = fields.Boolean('Is From Transportasi Wizard')
    is_from_ruang_semayam_wizard = fields.Boolean('Is From Ruang Semayam Wizard')
    jenis_tambahan_ruang_semayam = fields.Selection([
        ('hari', 'Tambah Hari'),
        ('lebar', 'Tambah Lebar'),
    ], string='Jenis Tambahan Ruang Semayam')
    is_ruang_semayam = fields.Boolean(compute='_compute_is_ruang_semayam', string='Is Ruang Semayam', store=True)
    @api.depends('product_id','product_warehouse_id','product_uom_qty','price_unit')
    def _compute_is_ruang_semayam(self):
        for record in self:
            try:
                ruang_semayam_category_id = self.env.ref('custom_sale_order.categ_ruang_semayam')
            except:
                ruang_semayam_category_id = False
            record.is_ruang_semayam = False
            if record.product_id and ruang_semayam_category_id and record.product_id.product_tmpl_id.categ_id.id == ruang_semayam_category_id.id:
                record.is_ruang_semayam = True

    is_columbarium = fields.Char(compute='_compute_is_columbarium', string='Is Columbarium', store=True)
    @api.depends('product_id','product_warehouse_id','product_uom_qty','price_unit')
    def _compute_is_columbarium(self):
        for record in self:
            try:
                columbarium_category_id = self.env.ref('custom_sale_order.categ_columbarium')
            except:
                columbarium_category_id = False
            record.is_columbarium = False
            if record.product_id and columbarium_category_id and record.product_id.product_tmpl_id.categ_id.id == columbarium_category_id.id:
                record.is_columbarium = True

    is_readonly = fields.Boolean(compute='_compute_is_readonly', string='Is Readonly')
    is_amount_readonly = fields.Boolean(compute='_compute_is_readonly', string='Is Readonly')
    
    @api.depends(
        'order_id',
        'product_id',
        'product_id.product_tmpl_id',
        'product_id.product_tmpl_id.categ_id',
        'name',
        'is_from_transportasi_wizard',
        'is_from_ruang_semayam_wizard')
    def _compute_is_readonly(self):
        for record in self:
            categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
            categ_ruangdoa = self.env.ref('custom_sale_order.categ_ruangdoa')
            
            record.is_readonly = False
            record.is_amount_readonly = False
            if record.is_from_transportasi_wizard or record.is_from_ruang_semayam_wizard or record.product_id.product_tmpl_id.categ_id.id in [categ_columbarium.id,categ_ruangdoa.id]:
                record.is_readonly = True
                
            if record.product_id.uneditable_price_so:
                record.is_amount_readonly = True

    cost_sheet_line_id = fields.Many2one('cost.sheet.line', compute='_compute_cost_sheet_line_id', string='Cost Sheet Line', store=True)
    @api.depends('order_id.cost_sheet_id','order_id.cost_sheet_id.cost_sheet_line')
    def _compute_cost_sheet_line_id(self):
        for record in self:
            if record.order_id.cost_sheet_id:
                cost_sheet_line_ids = record.order_id.cost_sheet_id.cost_sheet_line.filtered(lambda x: x.sale_order_line_id.id == record.id)
                if cost_sheet_line_ids:
                    record.cost_sheet_line_id = cost_sheet_line_ids[0].id
                elif record.id and record.product_id and (record.product_id.detailed_type in ['consu','service'] or record.product_id.is_konsinyasi):
                    # kalau gaada cost_sheet_line_id maka create
                    cost_sheet_line_id = self.env['cost.sheet.line'].create({
                        'cost_sheet_id': record.order_id.cost_sheet_id.id,
                        'sale_order_line_id': record.id,
                        'product_id':record.product_id.id,
                        'name': record.name,
                        'budget_cost':0
                    })
                    record.cost_sheet_line_id = cost_sheet_line_id.id

    # memastikan produk jenis pack tidak dipilih melalui sale order line
    # set warehouse untuk product biasa dan konsinyasi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                # record.product_warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.main_warehouse_id')) if not record.product_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id'))
                record.product_warehouse_id = record.product_id.product_tmpl_id.default_stock_warehouse_id.id if not record.product_id.is_konsinyasi else int(self.env['ir.config_parameter'].sudo().get_param('custom_sale_order.kons_warehouse_id'))
            if record.product_id.ni_is_product_pack and not record.paket_id:
                record.product_id = None
                raise UserError('You can only select Pack Product from "Add Pack" Button')
            


    # @api.onchange('product_id')
    # def _onchange_product_id_validation(self):
    #     for record in self:
    #         if record.free_qty < record.product_uom_qty:
            
    #             okey = self._context.get('okey',False)
    #             if not okey:
    #                 context = {
    #                     'default_message': "Stock tidak cukup",
    #                     # 'default_data_id':record.id,
    #                     # 'default_model_name':record._name,
    #                     # 'default_function_name':"action_confirm",
    #                     # 'default_function_parameter':record.,
    #                 }
    #                 return{
    #                     'type':'ir.actions.act_window',
    #                     'name':'Alert',
    #                     'res_model':'confirm.wizard',
    #                     'view_type':'form',
    #                     'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_view_3').id,
    #                     # 'view_type':'ir.actions.act_window',
    #                     'view_mode':'form',
    #                     'target':'new',
    #                     'context':context                
    #                     }

    ###############################################################
    ##   OVERRIDED METHOD
    ############################################################### 

    # OVERRIDED FROM `sale_stock` MODULE
    # action_product_forecast_report untuk open forecasted report
    # refer warehouse di widgetnya sudah sesuai, tp pada saat open reportnya tidak sesuai warehousenya
    @api.depends(
        'product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.commitment_date',
        'move_ids', 'move_ids.forecast_expected_date', 'move_ids.forecast_availability', 'product_warehouse_id')
    def _compute_qty_at_date(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
        1. The quotation has a commitment_date, we take it as delivery date
        2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        treated = self.browse()
        # If the state is already in sale the picking is created and a simple forecasted quantity isn't enough
        # Then used the forecasted data of the related stock.move
        for line in self.filtered(lambda l: l.state == 'sale'):
            if not line.display_qty_widget:
                continue
            moves = line.move_ids.filtered(lambda m: m.product_id == line.product_id)
            line.forecast_expected_date = max(moves.filtered("forecast_expected_date").mapped("forecast_expected_date"), default=False)
            line.qty_available_today = 0
            line.free_qty_today = 0
            for move in moves:
                line.qty_available_today += move.product_uom._compute_quantity(move.reserved_availability, line.product_uom)
                line.free_qty_today += move.product_id.uom_id._compute_quantity(move.forecast_availability, line.product_uom)
            line.scheduled_date = line.order_id.commitment_date or line._expected_date()
            line.virtual_available_at_date = False
            treated |= line

        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self.filtered(lambda l: l.state in ('draft', 'sent')):
            if not (line.product_id and line.display_qty_widget):
                continue
            # old
            # grouped_lines[(line.warehouse_id.id, line.order_id.commitment_date or line._expected_date())] |= line
            # overrided
            grouped_lines[(line.product_warehouse_id.id, line.order_id.commitment_date or line._expected_date())] |= line

        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id]
                line.forecast_expected_date = False
                product_qty = line.product_uom_qty
                if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
                    product_qty = line.product_uom._compute_quantity(product_qty, line.product_id.uom_id)
                qty_processed_per_product[line.product_id.id] += product_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False


    def unlink(self):
        for record in self:
            # raise UserError(self.ids)
            # kalau delete paket, maka semua itemnya didelete
            if record.paket_id:
                item_list = self.env[record._name].search([
                    ('order_id','=',record.order_id.id),
                    ('parent_id','=',record.id)
                ])
                item_list.filtered(lambda x: x.id not in self.ids).unlink()

                # delete juga tiket parkir
                if record.order_id and record.order_id.voucher_parkir_ids:
                    record.order_id.voucher_parkir_ids = False

            # kalau delete item paket
            if record.parent_id:
                deleted_order_line = self.env['sale.order.line.deleted'].create({
                    'order_id': record.order_id.id,
                    'product_id': record.product_id.id,
                    'name': record.name,
                    'product_warehouse_id': record.product_warehouse_id.id,
                    'product_uom_qty': record.product_uom_qty,
                    'product_uom': record.product_uom.id,
                    'price_unit': record.price_unit,
                    'tax_id': record.tax_id.ids,
                    'price_subtotal': record.price_subtotal,
                })

                record.order_id.message_post(body="<b style='color:red;'>Item Paket yang dihapus</b> : <br/><br/>Product : {product_name}<br/>Desc : {desc}<br/>Unit : {unit}".format(
                    product_name = deleted_order_line.product_id.name,
                    desc = deleted_order_line.name,
                    unit = deleted_order_line.product_uom_qty,
                ))

            # kalau yang di delete merupakan produk pengganti, balikin qtynya jadi 
            if record.is_produk_pengganti:
                order_lines = record.order_id.order_line.filtered(lambda x: x.pengganti_id.id == record.id)
                if order_lines:
                    for line in order_lines:
                        paket_id = line.parent_id.paket_id.ni_bundle_product_ids.filtered(lambda x: x.name.id == line.product_id.product_tmpl_id.id)
                        if paket_id:
                            line.product_uom_qty = paket_id[0].ni_quantity
                        else:
                            line.product_uom_qty = record.product_uom_qty
                    
                        # CASE KALAU YANG DIAKUI DI COLUMBARIUM ITU KESELURUHAN HARGA COLUMBARIUM
                        # kalau yang diganti columbarium maka balikin harganya parent paketnya
                        # categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
                        # if line.product_id.product_tmpl_id.categ_id.id == categ_columbarium.id and line.parent_id:
                        #     packet_line = line.parent_id.product_id.product_tmpl_id.ni_bundle_product_ids.filtered(lambda x : x.name.id == line.product_id.product_tmpl_id.id)
                        #     if packet_line:
                        #         line.parent_id.price_unit += packet_line.price

                record.order_id.cost_sheet_id.set_vendor_list()


        return super(SaleOrderLine, self).unlink()

    ###############################################################
    ##  METHOD
    ###############################################################    
    
    # validasi produk paket jenis ruang semayam tidak boleh diganti
    def validate_change_pack_ruang_semayam(self):
        for record in self:
            if record.is_ruang_semayam:
                raise UserError("Produk dengan kategori Ruang Semayam tidak boleh di ganti!")

    # untuk ganti produk paket
    def action_change_pack_item(self):
        for record in self:
            # record.validate_change_pack_ruang_semayam()

            result = {
                'name': _('Ganti Produk'), 
                'view_type': 'form', 
                'view_mode': 'form', 
                'view_id': self.env.ref('custom_sale_order.change_product_wizard_view').id, 
                'res_model': 'change.product.wizard', 
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_so_id': record.order_id.id,
                    'default_so_line_id': record.id,
                    'default_pickup_date_new': record.pickup_date if record.pickup_date else None,
                    'default_return_date_new': record.return_date if record.return_date else None,
                }
            }
            return result  
            

class SaleOrderLineDeleted(models.Model):
    _name = 'sale.order.line.deleted'

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete="cascade")
    currency_id = fields.Many2one(related="order_id.currency_id")
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char('Description')
    product_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    product_uom_qty = fields.Float('Kuantitas')
    product_uom = fields.Many2one('uom.uom', string='Satuan')
    price_unit = fields.Float('Harga Satuan')
    tax_id = fields.Many2many('account.tax', string='Pajak')
    price_subtotal = fields.Float('Subtotal')