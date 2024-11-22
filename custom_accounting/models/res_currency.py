from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import date, datetime

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _set_idr_currency_precission(self):
        # get idr ids
        curr = self.env.ref('base.IDR')

        if curr:
            query = '''
                update res_currency
                set rounding = 1, decimal_places = 0
                where id = {curr_id} and rounding != 1
            '''.format(
                curr_id = curr.id
            )
            self.env.cr.execute(query)