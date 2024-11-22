from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

# import function
import sys, os
path = os.path.dirname(os.path.realpath(__file__)) # get current location of directory
parent_directory, directory_name = os.path.split(path) # get parent path
func_dir = parent_directory + "/function/" # function module
sys.path.append(func_dir)
from function import send_whatsapp_message

from babel.dates import format_date, format_datetime, format_time
from datetime import datetime, timedelta, date

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_phone = fields.Char(related="partner_id.phone", readonly=False)
    reference_id = fields.Char('No. Reference')
    status_whatsaapp = fields.Char('Status')

    ###############################################################
    ##   METHOD
    ############################################################### 
    # @api.constrains('partner_phone','partner_id.phone')
    # def _constrains_partner_phone(self):
    #     for record in self:
    #         if record.partner_phone:
    #             if not record.partner_phone.isnumeric():
    #                 raise ValidationError("Nomor telepon hanya boleh diisi dengan angka!\n\n{po_name}".format(
    #                     po_name = record.name,
    #                 ))


    # prepare send whatsapp

    def prepare_send_whatsapp(self,template,body_template):
        for record in self:
            # validasi
            if not record.partner_phone:
                raise ValidationError("{partner} tidak memiliki nomor telepon. Silahkan isi no telepon yang terdaftar ke whatsapp sebelum kirim pesan Whatsapp!\n\n{no_po}".format(
                    no_po = record.name,
                    partner = record.partner_id.name    
                ))
            
            credentials = {}
            wa_cred = self.env['whatsapp.credentials'].search([('is_activate','=',True)],limit=1)
            if wa_cred:
                credentials = list(map(lambda x: {
                    'url' : x.url,
                    'clientSid' : x.clientSid,
                    'key' : x.key,
                    'password' : x.password ,
                }, wa_cred))[0]


            result = send_whatsapp_message(
                credentials = credentials,
                # to = '6287825529016',
                to = record.partner_id.phone,
                template = template,
                body_template = body_template
            )
            return result

    # untuk send whatsapp semayam
    def action_send_whatsapp(self):
        for record in self:
            product = ""
            jumlah = ""
            for line in record.order_line:
                product = line.product_id.display_name
                jumlah = "{jumlah} {uom}".format(
                    jumlah = int(round(line.product_qty,0)),
                    uom = line.product_uom.name
                )
                break

            body_template = {
                "{{1}}": record.partner_id.name,
                "{{2}}": format_datetime(record.date_planned+timedelta(hours=7), format="dd MMMM yyy", locale='id_ID'),
                "{{3}}": product,
                "{{4}}": jumlah,
                "{{5}}": format_datetime(record.date_planned+timedelta(hours=7), format="H:mm 'WIB'", locale='id_ID'),
                "{{6}}": format_datetime(record.date_planned+timedelta(hours=7), format="EEEE',' dd MMMM yyy", locale='id_ID'),
                "{{7}}": record.cost_sheet_id.sale_order_id.partner_id.name,
                "{{8}}": record.cost_sheet_id.sale_order_id.penanggungjawab_id.name,
                "{{9}}": record.cost_sheet_id.sale_order_id.ruang_semayam_id.display_name,
                "{{10}}": record.user_id.name,
            }

            result = record.prepare_send_whatsapp(
                template = 'info_order_rdc_bold',
                body_template = body_template
            )

            # raise UserError(str(result))
            if result:
                record.reference_id = result.get('refId')
                record.status_whatsaapp = result.get('rm')

                if len(self) == 1 and result.get('rc'):
                    message = ""
                    if result.get('rc') == "1":
                        message = "Pesan Whatsapp telah terkirim!"
                    else:
                        message = "Pesan Whatsapp gagal dikirim!\n\n{result}".format(
                            result= result.get('rm') if result.get('rm') else ""
                        )

                    if message:
                        return  {
                            'type':'ir.actions.act_window',
                            'name':'Alert',
                            'res_model':'confirm.wizard',
                            'view_type':'form',
                            'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_view_3').id,
                            # 'view_type':'ir.actions.act_window',
                            'view_mode':'form',
                            'target':'new',
                            'context':{
                                'default_message': message,
                                'default_data_id':record.id,
                                'default_model_name':record._name,
                                'default_function_name':"action_send_whatsapp",
                                # 'default_function_parameter':record.,
                            }                
                        }

    # untuk send whatsapp penawaran
    def action_send_whatsapp_penawaran(self):
        for record in self:
            body_template = {
                "{{1}}": record.partner_id.name,
                # "{{2}}": record.date_order.strftime("%d/%m/%Y, Pukul %H:%M:%S"),
                # "{{2}}": format_datetime(record.date_order, format="EEEE, dd MMM yyy 'pukul' H:mm 'WIB'", locale='id_ID'),
                "{{2}}": format_datetime(record.date_order+timedelta(hours=7), format="dd MMMM yyy 'pukul' H:mm 'WIB'", locale='id_ID'),
                "{{3}}": "1. -",
                "{{4}}": "2. -",
                "{{5}}": "3. -",
                "{{6}}": "4. -",
                "{{7}}": "5. -",
                "{{8}}": "6. -",
                "{{9}}": "7. -",
                "{{10}}": "8. -",
                "{{11}}": "9. -",
                "{{12}}": "10. -",
            }
            
            for i,line in enumerate(record.order_line,3):
                if body_template.get("{{%s}}" % i):
                    body_template["{{%s}}" % i] = body_template["{{%s}}" % i][:-1] + "{product}, {qty} {uom}".format(
                        product = line.name,
                        qty = int(round(line.product_qty,0)),
                        uom = line.product_uom.name
                    )
            result = record.prepare_send_whatsapp(
                template = 'template_po2',
                body_template = body_template
            )
            
            # raise UserError(str(result))
            if result:
                record.reference_id = result.get('refId')
                record.status_whatsaapp = result.get('rm')

                if len(self) == 1 and result.get('rc'):
                    message = ""
                    if result.get('rc') == "1":
                        message = "Pesan Whatsapp telah terkirim!"
                    else:
                        message = "Pesan Whatsapp gagal dikirim!\n\n{result}".format(
                            result= result.get('rm') if result.get('rm') else ""
                        )

                    if message:
                        return  {
                            'type':'ir.actions.act_window',
                            'name':'Alert',
                            'res_model':'confirm.wizard',
                            'view_type':'form',
                            'view_id': self.env.ref('custom_sale_order.confirm_wizard_form_view_3').id,
                            # 'view_type':'ir.actions.act_window',
                            'view_mode':'form',
                            'target':'new',
                            'context':{
                                'default_message': message,
                                'default_data_id':record.id,
                                'default_model_name':record._name,
                                'default_function_name':"action_send_whatsapp",
                                # 'default_function_parameter':record.,
                            }                
                        }