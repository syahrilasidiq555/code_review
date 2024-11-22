from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo import SUPERUSER_ID

class hr_job(models.Model):
    _inherit = 'hr.job'

    is_worker_level = fields.Boolean('Is Worker Level')
    is_admin_level = fields.Boolean('Is Admin Level')