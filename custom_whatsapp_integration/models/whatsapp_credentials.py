from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict


class WhatsappCredentials(models.Model):
    _name = 'whatsapp.credentials'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Whatsapp Credentials"
    _rec_name = "clientSid"

    url = fields.Char('URL')
    clientSid = fields.Char('Client SID')
    key = fields.Char('Key')
    password = fields.Char('Password')

    is_activate = fields.Boolean('Active')

    @api.constrains('clientSid')
    def _constrains_clientSid(self):
        for record in self:
            if record.clientSid:
                credentials_ids = self.env[record._name].search([
                    ('id','!=',record.id),
                    ('clientSid','=',record.clientSid)
                ])
                if credentials_ids:
                    raise ValidationError("Client SID telah diisi sebelumnya!")


    def action_activate(self):
        for record in self:
            if len(self) > 1:
                raise ValidationError("Hanya boleh aktifkan 1 credentials!")
            
            record.is_activate = True

            credentials_ids = self.env[record._name].search([
                ('id','!=',record.id),
                ('is_activate','=',True)
            ])
            for cred in credentials_ids:
                cred.is_activate = False
                