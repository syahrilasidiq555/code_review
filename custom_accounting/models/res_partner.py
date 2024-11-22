# from attr import field
from unicodedata import category
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # untuk penanda vendor
    is_vendor = fields.Boolean(string="Sebagai Vendor", default=False, store=True, tracking=True)

    # untuk penanda customer
    is_customer = fields.Boolean(string="Sebagai Customer", default=False, store=True, tracking=True)

#     # inherit utk set default 
#     lang = fields.Selection(default="id_ID")

# class Lang(models.Model):
#     _inherit = "res.lang"

#     @api.model
#     @tools.ormcache()
#     def get_installed(self):
#         """ Return the installed languages as a list of (code, name) sorted by name. """
#         langs = self.with_context(active_test=True).search([])
#         return sorted([(lang.code, lang.name) for lang in langs], key=itemgetter(2))