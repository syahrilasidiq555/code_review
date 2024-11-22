from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

_STATES = [
    ('draft','Draft'),
    ('confirm', 'Confirm'),
]

class HrPayslipPremi(models.Model):
    _name = 'hr.payslip.premi'
    _description = "Employee Premi"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "name desc"

    name = fields.Char(string="Name", default=lambda self: ('New'), copy=False, index=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule", required=True, 
        domain=[('appears_on_premi','=',True),('active','=',True)])
    state = fields.Selection(selection=_STATES, string="Status", index=True,  tracking=True, 
        copy=False, default="draft")
    type_length = fields.Selection(string='Type Length', 
        selection=[
            ('month', 'Month'), 
            ('year', 'Year')])
    premi_line = fields.One2many('hr.payslip.premi.line','premi_id', string="Premi Lines", ondelete='cascade', copy=True, tracking=True)

    def action_confirm(self):
        self.write({'state':'confirm'})

    def action_reset_to_draft(self):
        self.write({'state':'draft'})

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            tmpName = self.env['ir.sequence'].next_by_code('hr.premi.number') or ('New')
            vals['name'] = tmpName
            
        result = super(HrPayslipPremi, self).create(vals)
        return result

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("You can't delete Confirmed Salary Correction.")
            
        result = super(HrPayslipPremi, self).unlink()
        return result

class HrPayslipPremiLine(models.Model):
    _name = "hr.payslip.premi.line"
    _description = "Emplyoee Premi Line"
    
    premi_id = fields.Many2one('hr.payslip.premi', string='Employee Premi', readonly=True, copy=False)
    start_length_of_work = fields.Integer(string="Start", required=True)
    end_length_of_work = fields.Integer(string="End", required=True)
    type_length = fields.Selection(related='premi_id.type_length')
    amount = fields.Float(string="Amount", required=True)