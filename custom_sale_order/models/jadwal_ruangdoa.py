from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

import math

class jadwalRuangdoa(models.Model):
    _name = "jadwal.ruangdoa"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Jadwal Ruang Doa"
    _rec_name = 'dayofweek'

    dayofweek = fields.Selection([
        ('0', 'Senin'),
        ('1', 'Selasa'),
        ('2', 'Rabu'),
        ('3', 'Kamis'),
        ('4', 'Jumat'),
        ('5', 'Sabtu'),
        ('6', 'Minggu')
        ], string='Hari', required=True, default='0')
    hour_from = fields.Float(string='Mulai', required=True,
        help="Start and End time of working.\n"
            "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Berakhir', required=True)


    def name_get(self):
        result = []
        for record in self:
            hour_from = "{jam}:{menit}".format(
                jam= int(record.hour_from),
                menit= int(round((record.hour_from % 1)*60,1))
            )
            hour_to = "{jam}:{menit}".format(
                jam= int(record.hour_to),
                menit= int(round((record.hour_to % 1)*60,1))
            )
            name = "{hari} ({hour_from} - {hour_to})".format(
                hari=dict(self._fields['dayofweek'].selection).get(record.dayofweek),
                hour_from=hour_from,
                hour_to=hour_to,
            )
            result.append((record.id, name))
        return result

    
    @api.constrains('dayofweek','hour_from','hour_to')
    def _constrains_dayofweek(self):
        for record in self:
            jadwal = self.env[self._name].search([
                ('id','!=', record.id),
                ('dayofweek','=', record.dayofweek),
                ('hour_to','>', record.hour_from),
                ('hour_from','<', record.hour_to),
            ])
            if jadwal:
                hour_from = "{jam}:{menit}".format(
                    jam= int(jadwal.hour_from),
                    menit= int(round((jadwal.hour_from % 1)*60,1))
                )
                hour_to = "{jam}:{menit}".format(
                    jam= int(jadwal.hour_to),
                    menit= int(round((jadwal.hour_to % 1)*60,1))
                )
                name = "{hari} ({hour_from} - {hour_to})".format(
                    hari=dict(self._fields['dayofweek'].selection).get(jadwal.dayofweek),
                    hour_from=hour_from,
                    hour_to=hour_to,
                )
                message = "Jam dan hari yang anda masukan overlap dengan jadwal berikut:\n\n%s" % (name)
                raise ValidationError(message)