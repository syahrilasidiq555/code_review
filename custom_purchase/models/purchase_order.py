from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _order = 'priority desc, date_order desc, id desc'

    yes_no = fields.Selection(string='Pilihan', selection=[('yes', 'Akan melakukan komparasi'), ('no', 'Tidak akan melakukan komparasi')])
    alasan = fields.Text(string='Alasan')

    # Nomor PO yg sdh di approve
    purchase_name = fields.Char(string='Purchase Order', store=True, readonly=False, default=lambda self: ('New'))

    # Jika PO tsb digenerate dari Permintaan Barang, maka tidak boleh lagi menambahkan produk lain lagi
    is_editable = fields.Boolean(compute="_compute_is_editable", readonly=True)
    @api.depends("state","order_line.purchase_request_id")
    def _compute_is_editable(self):
        for rec in self:
            rec.is_editable = len(rec.order_line.filtered(lambda x: x.purchase_request_id.id != False)) == 0

    def button_confirm(self, komparasi=None):
        # hasil dari wizard jika tanpa komparasi, langsung jalani button_confirm
        if komparasi == False:
            res = super(PurchaseOrder, self).button_confirm()
            return res

        # jika hasil akan di komparasi, maka masuk ke logic di bawah ini
        is_compare = self.env['ir.config_parameter'].sudo().get_param('custom_purchase.is_compare_vendor')
        if is_compare:
            list_brg = ""
            compare_amount = self.env['ir.config_parameter'].sudo().get_param('custom_purchase.compare_vendor_amount')
            count_compare_vendor = self.env['ir.config_parameter'].sudo().get_param('custom_purchase.min_count_compare_vendor')
            if self.yes_no:
                if self.yes_no == 'yes':
                    for i in self.order_line:
                        # cek jika rfq dari purchase request belum memenuhi counting by config system
                        # masuk ke logic sini, karna user sdh menentukan pilihan 'yes' saat di wizard
                        if int(len(i.purchase_request_lines.purchase_lines)) < int(count_compare_vendor):
                            list_brg += "- " + i.product_id.name + " (" + i.name + ") = {count} Vendor\n".format(count=str(len(i.purchase_request_lines.purchase_lines)))
                    if list_brg != "":
                        desc = "Terdapat barang yang belum dicompare dengan {count} Vendor : \n {list_brg}".format(
                            compare_amount=compare_amount,
                            count=count_compare_vendor,
                            list_brg=list_brg
                        )
                        raise ValidationError(desc)
                    else:
                        res = super(PurchaseOrder, self).button_confirm()
                        return res
            else:
                for i in self.order_line:
                    if i.purchase_request_lines:
                        # cek jika nilai barang dan rfq dari purchase request belum memenuhi by config system
                        if float(i.price_subtotal) >= float(compare_amount) and int(len(i.purchase_request_lines.purchase_lines)) < int(count_compare_vendor):
                            list_brg += "- " + i.product_id.name + " (" + i.name + ") \n"

                if list_brg != "":
                    desc = "Terdapat nilai barang yang melebihi {compare_amount} dan belum dicompare dengan {count} Vendor : \n {list_brg}".format(
                        compare_amount=compare_amount,
                        count=count_compare_vendor,
                        list_brg=list_brg
                    )
                    result = {
                        'name': _('Komparasi Vendor'), 
                        'view_type': 'form', 
                        'view_mode': 'form', 
                        'view_id': self.env.ref('custom_purchase.view_purchase_notify_vendor_wizard').id, 
                        'res_model': 'purchase.notif.vendor', 
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {
                            'default_po_id': self.id,
                            'default_desc': desc,
                        }
                    }
                    return result
                else:
                    res = super(PurchaseOrder, self).button_confirm()
                    return res
        
        else:
            # jika di config tanpa komparasi, langsung jalanin button_confirm
            res = super(PurchaseOrder, self).button_confirm()
            return res
    

    total_printed = fields.Integer(string='Total Printed', tracking=True)
    def print_po(self):
        for record in self:
            record.sudo().write({
                'total_printed': record.total_printed + 1
            })
        # return self.env.ref('purchase.action_report_purchase_order').report_action(self)
        return self.env.ref('custom_purchase.action_report_purchase_order_rdc').report_action(self)

    
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    purchase_request_id = fields.Many2one('purchase.request', related="purchase_request_lines.request_id")