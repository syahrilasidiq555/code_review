from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

_STATES = [
    ('draft','Draft'),
    ('confirm', 'Confirm'),
]

class HrPayslipCorrection(models.Model):
    _name = 'hr.payslip.correction'
    _description = "Salary Correction"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "name desc"

    name = fields.Char(string="Name", default=lambda self: ('New'), copy=False, index=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    employee_id = fields.Many2one('hr.employee', copy=False, string="Employee", required=True)
    barcode = fields.Char(string="NIK", related='employee_id.barcode')
    identification_id = fields.Char(string="No. KTP", related='employee_id.identification_id')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Department")
    section_id = fields.Many2one('hr.department', related='employee_id.section', string="Section")
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string="Jabatan Lama")

    pay_mode = fields.Selection(
        string='Payment Mode',
        selection=[
            ('full', 'One Time'), 
            ('installment', 'Installment')], required=True)

    @api.onchange('pay_mode')
    def _onchange_pay_mode(self):
        self.pay_count = 1 if self.pay_mode == 'full' else 0

    @api.constrains('pay_count')
    def _constrains_pay_count(self):
        for rec in self:
            if rec.pay_count == 0:
                raise UserError("Pay Count must be greater than 0.")

    pay_periode = fields.Date(string="Payment Periode", track_visibility='onchange', required=True, default=fields.Datetime.now)
    pay_count = fields.Integer(string="Payment Count", required=True)
    description = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule", required=True, 
        domain=[('appears_on_correction','=',True),('active','=',True)])

    state = fields.Selection(selection=_STATES, string="Status", index=True,  tracking=True, 
        copy=False, default="draft")
    
    correction_detail = fields.One2many('hr.payslip.correction.detail','correction_id', string="Correction Detail", ondelete='cascade', copy=True, tracking=True)
    
    def generate_payment(self):
        app_inf = []
        for i in range(self.pay_count):
            self.correction_detail = False
            tmp = [0,0,{
                'description': 'Pembayaran {} ke {}'.format(self.description, i+1),
                'due_date': self.pay_periode + relativedelta(months=i),
                'amount': self.amount / self.pay_count,
            }]
            app_inf.append(tmp)
        self.correction_detail = app_inf

    @api.onchange('pay_periode','pay_mode','description','amount')
    def _onchange_payment(self):
        for rec in self:
            rec.generate_payment()

    def action_confirm(self):
        self.write({'state':'confirm'})

    def action_reset_to_draft(self):
        for correction in self.correction_detail:
            if correction.is_pay:
                raise ValidationError("Cannot reset to draft, some Correction already paid.")

        self.write({'state':'draft'})

    @api.model
    def create(self, vals):
        self.generate_payment()
        if vals.get('name', ('New')) == ('New'):
            tmpName = self.env['ir.sequence'].next_by_code('salary.correction.number') or ('New')
            vals['name'] = tmpName
            
        result = super(HrPayslipCorrection, self).create(vals)
        return result
    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("You can't delete Confirmed Salary Correction.")
            
            result = super(HrPayslipCorrection, rec).unlink()
        return result
    

class HrPayslipCorrectionDetail(models.Model):
    _name = 'hr.payslip.correction.detail'
    _description = "Salary Correction Detail"

    correction_id = fields.Many2one('hr.payslip.correction',  string='Salary Correction Detail', readonly=True, copy=False)
    description = fields.Char(string='Description', tracking=True)
    due_date = fields.Date(string="Due Date")
    amount = fields.Float(string="Amount")
    is_pay = fields.Boolean(default=False, string="is Paid ?")
