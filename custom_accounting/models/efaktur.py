# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import re


class Efaktur(models.Model):
    _inherit = "l10n_id_efaktur.efaktur.range"
    _description = "Available E-faktur range"

    prefix = fields.Char(store=True, readonly=False)

    @api.model
    def pop_number_2(self, company_id):
        range = self.search([('company_id', '=', company_id)], order="min ASC", limit=1)
        if not range:
            return None

        popped = int(range.min)
        if int(range.min) >= int(range.max):
            range.unlink()
        else:
            range.min = '%013d' % (popped + 1)
        return popped, range