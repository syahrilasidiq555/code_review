from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class hr_kompensasi_pkwt(models.Model):
    _name = 'hr.kompensasi.pkwt'
    _description = "Kompensasi PKWT"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string="Name", default=lambda self: ('New'), copy=False, index=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', copy=False, string="Employee")
    barcode = fields.Char(string="NIK", related='employee_id.barcode')
    identification_id = fields.Char(string="No. KTP", related='employee_id.identification_id')
    
    contract_id = fields.Many2one('hr.contract', string="Contract", related="employee_id.contract_id")
    @api.constrains('contract_id')
    def _constrains_contract_id(self):
        for rec in self:
            if rec.contract_id.is_generate_pkwt:
                raise ValidationError("Current contract on Employee {} already have PKWT.".format(rec.employee_id.name))

    start_contract_date = fields.Date(string="Start Contract", default=fields.Datetime.now, related="contract_id.date_start", track_visibility='onchange')
    end_contract_date = fields.Date(string="End Contract", default=fields.Datetime.now, related="contract_id.date_end",track_visibility='onchange')
    contract_periode = fields.Selection(
        string='Contract Periode',
        selection=[
            ('', ''), 
            ('1', '1 Bulan'), 
            ('2', '2 Bulan'),
            ('3', '3 Bulan'),
            ('4', '4 Bulan'),
            ('5', '5 Bulan'),
            ('6', '6 Bulan'),
            ('7', '7 Bulan'),
            ('8', '8 Bulan'),
            ('9', '9 Bulan'),
            ('10', '10 Bulan'),
            ('11', '11 Bulan'),
            ('12', '12 Bulan'),
        ], tracking=True)
    
    @api.onchange('employee_id','contract')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.contract_id:
                d0 = date(self.start_contract_date.year, self.start_contract_date.month, self.start_contract_date.day)
                d1 = date(self.end_contract_date.year, self.end_contract_date.month, self.end_contract_date.day) + timedelta(days=1)
                
                diff = relativedelta(d1, d0)
                periode = ((diff.years * 12) + diff.months)
                if periode> 12:
                    raise ValidationError("Maximal contract periode is 12 Month")
                self.contract_periode = str(periode) if periode > 0 else ''
            else:
                self.contract_periode = ''
    
    bank_id = fields.Many2one('res.bank', string="Bank Name", related='employee_id.bank_id')
    bank_account_number = fields.Char(string="Bank Account Number", related='employee_id.bank_account_number')
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, default=lambda self: self.env.user.company_id.currency_id.id)
    base_salary = fields.Monetary(string='Base Salary', default=0.0, related="contract_id.wage", store=True, readonly=False)
    amount_kompensasi = fields.Monetary(string='Amount Kompensasi', default=0.0, compute='_compute_kompensasi')
    
    @api.depends('base_salary','contract_periode')
    def _compute_kompensasi(self):
        for rec in self:
            if rec.contract_id and self.contract_periode  != '':
                rec.amount_kompensasi = (int(rec.contract_periode) / 12) * rec.base_salary
            else:
                rec.amount_kompensasi = 0

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('kompensasi.pkwt.number') or ('New')

        result = super(hr_kompensasi_pkwt, self).create(vals)
        if result:
            result.contract_id.sudo().write({'is_generate_pkwt': True})
        return result
    
    def unlink(self):
        self.contract_id.sudo().write({'is_generate_pkwt': False})
        result = super(hr_kompensasi_pkwt, self).unlink()
        return result
    