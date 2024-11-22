from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re, html_escape, is_html_empty
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_rp = fields.Float() # ga perlu di tampilkan field ini mah ya, buat mancing aja
    discount_fixed = fields.Float(string='Disc Fixed', digits='Product Price', default=0.0)
    discount = fields.Float(digits=(12,12))

    @api.onchange("discount_fixed")
    def _onchange_discount_fixed(self):
        if self.discount_fixed:
            if self.price_unit > 0:
                self.discount = ((self.discount_fixed) / self.price_unit) * 100 or 0.00
            else:
                self.discount = 0 
        else:
            self.discount = 0 

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids', 'discount_fixed')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())

    def write(self, vals):
        if 'discount' in vals:
            if 'price_unit' in vals:
                vals['discount_fixed'] = (vals['price_unit'] * vals['discount']) / 100
            else:
                vals['discount_fixed'] = (self.price_unit * vals['discount']) / 100
        res = super(AccountMoveLine, self).write(vals)
        return res
    
    def _eligible_for_cogs(self):
        self.ensure_one()
        return self.product_id.type == 'product' and self.product_id.categ_id.is_cogs_inv # self.product_id.valuation == 'real_time' <- 
