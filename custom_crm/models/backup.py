from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import hashlib
import requests
import json

import random
import string

class CrmLead(models.Model):
    _inherit = "crm.lead"

    # UNTUK KEBUTUHAN WHATSAPP
    reference_id = fields.Char('No. Reference')
    status_whatsaapp = fields.Char('Status')

    def action_send_api_wa(self, cust_name, custom_phone, date_end):
        refId = ''.join(random.choices(string.ascii_uppercase, k=20)) #"VCUEQVIIPCDUSJUBJRKIZGYGTOYPWK"
        clientSid = "4450282D1B164D68A6B43AF40F024D52"
        key = "92496e46ca47468"
        password = "73121d14f6af422"
        nomor_hp = custom_phone
        nama_template = "template_crm_columbarium"
        language = "id"

        hash_string = refId + key + password
        sha_signature = self.encrypt_string(hash_string)
        
        url = "https://api.dial.id/waba/v2/message"

        # set body
        body = {
            "clientSid": clientSid,
            "refId": refId,
            "key": key,
            "to": nomor_hp,
            "auth": sha_signature,
            "template":{
                "name": nama_template,
                "language": language,
                "body": {
                    "{{1}}": cust_name,
                    "{{2}}": str(date_end)
                }
            }
        }
        data = json.dumps(body)
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=data)
            data = response.json()
            print(data)
        except:
            raise UserError("Gagal \n"+str(response.json()))

    def encrypt_string(self, hash_string):
        sha_signature = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
        return sha_signature

    def send_notif_columbarium_via_whatsapp(self, reminder_before_days=90):
        date = datetime.now().date() + timedelta(days=reminder_before_days)

        categ_columbarium = self.env.ref('custom_sale_order.categ_columbarium')
        record_rents = self.env['sale.rental.report'].search([('date','=',date),('product_id.categ_id','=',categ_columbarium.id)])
        
        for rec in record_rents:
            to = False
            if rec.partner_id.mobile:
                to = rec.partner_id.mobile
            elif rec.partner_id.phone:
                to = rec.partner_id.phone
            else:
                print('No Telp/Mobile pada Customer {partner_name} belum terdaftar pada system.'.format(partner_name=rec.partner_id.name))

            if to:
                # self.action_send_api_wa() # isi kebutuhannya

                #CREATE NEW OPPORTUNITY
                stage_new = self.env.ref('crm.stage_lead1')
                self.env['crm.lead'].sudo().create({
                    'name': rec.partner_id.name + ' Columbarium (' + rec.product_id.display_name + ')',
                    'email_from': rec.partner_id.email,
                    'phone': rec.partner_id.phone,
                    'partner_id': rec.partner_id.id,
                    'stage_id': stage_new.id,
                    'user_id': rec.order_id.user_id.id,
                    'type': 'opportunity',
                })