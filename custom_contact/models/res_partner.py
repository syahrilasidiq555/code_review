# from attr import field
from unicodedata import category
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
import json

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    customer_id = fields.Char(string='Customer ID', readonly=True)
    # _sql_constraints = [
    #     ('customer_id_uniq', 'unique (customer_id)', "Customer Id already exist.")
    # ]
    @api.constrains('customer_id')
    def _check_customer_id(self):
        for rec in self:
            if rec.customer_id:
                dt = self.env['res.partner'].search([('customer_id','=',rec.customer_id)])
                if len(dt) > 1:
                    raise ValidationError("Customer Id already exist.")
    
    segment_id = fields.Many2one('res.partner.segment', string='Segment')
    priority = fields.Selection(
        string='Priority',
        selection=[
            ('platinum', 'Platinum'), 
            ('gold', 'Gold'),
            ('silver', 'Silver'),
        ], compute="_compute_priority")
    
    @api.depends()
    def _compute_priority(self):
        for rec in self:
            now_date = date.today()
            date_begin = now_date + relativedelta(months=-1)
            date_begin = date(date_begin.year, date_begin.month, 1)
            date_end = date(date_begin.year, date_begin.month, calendar.monthrange(date_begin.year, date_begin.month)[1])
            
            dt = self.env['sale.order'].sudo().search([
                ('date_order','>=',date_begin),
                ('date_order','<=',date_end),
                ('state','=','sale'),
            ])
            amount = sum(dt.mapped('amount_total'))
            if amount >= 50000000:
                rec.priority = 'platinum'
            elif amount >= 10000000:
                rec.priority = 'gold'
            elif amount < 10000000:
                rec.priority = 'silver'

    customer_type = fields.Selection(
        string='Customer Type',
        selection=[
            ('end_customer', 'End Customer'), 
            ('reseller', 'Reseller'),
            ('internal', 'Internal'),
        ])

    def generate_customer_id(self):
        return self.env['ir.sequence'].with_context().next_by_code('customer.id.seq') or _('New')

    def open_wizard_change_customer_id(self):
        result = {
            'name': _('Change Customer ID'), 
            'view_type': 'form', 
            'view_mode': 'form', 
            'view_id': self.env.ref('custom_contact.res_partner_customer_id_form_wizard').id, 
            'res_model': 'res.partner.customerid.wizard', 
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_customer_id': self.customer_id,
            }
        }
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'customer_id' not in vals or vals['customer_id'] == '':
                vals['customer_id'] = self.generate_customer_id()
        moves = super().create(vals_list)
        return moves
    
class res_partner_segment(models.Model):
    _name = 'res.partner.segment'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Name already exist."),
    ]

    name = fields.Char(string="Segment", tracking=True)
    active = fields.Boolean(default="True", tracking=True)