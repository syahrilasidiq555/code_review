from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class masterTarifAmbulance(models.Model):
    _name = "master.tarif.ambulance"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread']
    _description = "Tarif Ambulance"
    _rec_name = "kota"


    kota = fields.Char('Kota', required=True)
    tarif = fields.Float('Tarif', digits="Product Price")
    
    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_default_currency_id)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s (%s %s)' % (record.kota,record.currency_id.symbol, f"{int(round(record.tarif,0)):,}")))
        return result