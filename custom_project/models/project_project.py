# from attr import field
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta

class Project(models.Model):
    _inherit = "project.project"

    project_number = fields.Char(string="Project Number", required=True, default=lambda self: _("New"), tracking=True)
    display_name = fields.Char(string="Name", compute="_compute_display_name")
    
    purchase_ids = fields.One2many('purchase.order', 'project_id', string='Purchase Order', ondelete='cascade', readonly=True)
    production_ids = fields.One2many('mrp.production', 'project_id', string='Manufacturing', ondelete='cascade', readonly=True)
    
    @api.depends('name','project_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "{} {}".format(rec.project_number, rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['project_number'] = self.env['ir.sequence'].with_context().next_by_code('project.project.seq') or _('New')
        res = super().create(vals_list)
        return res