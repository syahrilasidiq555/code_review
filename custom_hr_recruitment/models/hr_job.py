from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo import SUPERUSER_ID

class hr_job(models.Model):
    _inherit = 'hr.job'

    def _get_default_website_description(self):
        default_description = self.env.ref("custom_hr_recruitment.default_website_description", raise_if_not_found=False)
        return (default_description._render() if default_description else "")

    website_description = fields.Html(translate=html_translate, sanitize_attributes=False, default=_get_default_website_description, prefetch=False, sanitize_form=False)


    user_interviewer_id = fields.Many2one('res.users', string='User Interviewer')
    superviser_id = fields.Many2one('hr.employee', string='Job Superviser')