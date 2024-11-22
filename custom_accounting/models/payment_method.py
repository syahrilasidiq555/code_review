from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class PaymentMethod(models.Model):
    _name = "payment.method"
    _description = "Payment Method"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string='Name', required=True, tracking=True)
    journal_id = fields.Many2one(
        'account.journal', 
        string='Journal',
        ondelete='restrict', 
        tracking=True, 
        domain=[('type','in',['bank','cash']),('active','=',True)])
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    @api.model
    def create(self, vals):
        res = super(PaymentMethod, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(PaymentMethod, self).write(vals)
        return res