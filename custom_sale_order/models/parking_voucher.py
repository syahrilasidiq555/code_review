from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta, date


class ParkingVoucher(models.Model):
    _name = 'parking.voucher'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Parking Voucher"


    name = fields.Char('Kode Voucher', tracking=True)
    nama_pemakai = fields.Char('Nama Pemakai')
    date = fields.Datetime('Tanggal Masuk', required=True,tracking=True)
    # date_out = fields.Datetime('Tanggal Keluar', required=True, tracking=True)
    date_out = fields.Datetime(related="sale_order_id.tanggal_keluar", store=True)
    no_polisi = fields.Char('No. Polisi', tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Penjualan', tracking=True)
    customer_id = fields.Many2one(related="sale_order_id.partner_id", string="Nama Jenazah", store=True)
    ruang_semayam_id = fields.Many2one(related="sale_order_id.ruang_semayam_id", store=True)
    penanggungjawab_id = fields.Many2one(related="sale_order_id.penanggungjawab_id")

    jenis_kendaraan = fields.Selection([
        ('mobil', 'Mobil'),
    ], string='Kendaraan', default="mobil", required=True)

    ###############################################################
    ##   INHERITED METHOD
    ###############################################################

    @api.model
    def create(self, values):
        self.clear_caches()
        values['name'] = self.env['ir.sequence'].get_sequence(self._name,'RDC/PARK')
        res = super(ParkingVoucher,self).create(values)
        return res
    

    ###############################################################
    ##   METHOD
    ###############################################################

    # tombol view sales order
    def action_view_so(self):
        for record in self:
            if record.sale_order_id:
                form_view_id = self.env.ref("sale.view_order_form").id
                name = 'Sale Order'
                result = {
                    'name': _(name),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    # 'view_type': 'form',
                    'views': [(form_view_id, 'form')],
                    'res_id': record.sale_order_id.id,
                    'context': {'create': False},
                }
                return result  
            else:
                raise UserError("Sales Order Tidak Tersedia")
    