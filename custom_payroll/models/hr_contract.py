from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil import relativedelta

class hr_contract(models.Model):
    _inherit = 'hr.contract'


    travel_allowance = fields.Monetary(string="Uang Transportasi")
    uang_transportasi_staff = fields.Monetary(string="Uang Transportasi Staff")
    meal_allowance = fields.Monetary(string="Uang Makan")
    premi_masa_kerja_staff = fields.Monetary(string="Premi Masa Kerja Staff")
    insentif_kehadiran = fields.Monetary(string="Insentif Kehadiran")
    tunjangan_tdk_tetap = fields.Monetary(string="Tunjangan Tidak Tetap")
    premi_kebijakan = fields.Monetary(string="Premi Kebijakan")


    umk_id = fields.Many2one('master.umk', string='UMK Daerah', required=True)


    salary_type = fields.Selection([
        ('manual', 'Manual'),
        ('master', 'Based on Master UMK/UMR')
    ], string='Salary Type', default="manual", required=True)
    wage_id = fields.Many2one('master.umk', string='UMK/UMR')


    # wage history
    wage_history_ids = fields.One2many('hr.contract.wage_history', 'contract_id', string='Wage History')


    def set_salary_history(self,wage,date):
        for record in self:
            wage_history_ids = [[0,0,{
                'wage': wage,
                'applied_date': date,
            }]]
            record.wage_history_ids = wage_history_ids


    @api.model
    def create(self, vals):
        result = super(hr_contract, self).create(vals)
        if result:
            result.set_salary_history(result.wage, result.create_date.date())
        return result
    

    ####################################
    # Function for salary rule
    ####################################
    def get_current_umk_amount(self, umk_id, date_to):
        for record in self:
            umk = 0
            umk_history = self.env['master.umk.history'].sudo().search([
                ('umk_id','=',umk_id),
                # ('applied_date','>=',payslip.date_from),
                ('applied_date','<=',date_to),
            ], order="applied_date desc", limit=1)
            if umk_history:
                umk = umk_history[0].umk_amount
        return umk

    def get_umk_amount(self, payslip_id):
        for record in self:
            umk = 0
            payslip = self.env['hr.payslip'].sudo().browse(payslip_id)
            if payslip:
                umk = record.get_current_umk_amount(record.umk_id.id, payslip.date_to)
            return umk

    def get_premi_masa_kerja_amount(self, payslip_id, rule_code, type_length='year'):
        for record in self:
            amount = 0
            payslip = self.env['hr.payslip'].sudo().browse(payslip_id)
            rule = self.env['hr.salary.rule'].sudo().search([('code','=',rule_code)], limit=1)
            if payslip and rule:
                join_date = payslip.employee_id.join_date
                payslip_date = payslip.date_to

                delta = relativedelta.relativedelta(payslip_date, join_date)
                year_float = delta.years + (delta.months/12) + (delta.days/365)


                # get premi masa kerja
                premi = self.env['hr.payslip.premi'].sudo().search([
                    ('state','=','confirm'),
                    ('salary_rule_id','=',rule.id),
                    ('type_length','=',type_length)
                ],order="id desc",limit=1)
                if premi:
                    line = premi.premi_line.filtered(lambda x: x.start_length_of_work <= year_float and x.end_length_of_work >= year_float)
                    amount = line[0].amount if line else 0
            return amount

    def get_inputs_amount(self, payslip_id, rule_code):
            amount = 0
            payslip = self.env['hr.payslip'].sudo().browse(payslip_id)
            if payslip and payslip.input_line_ids:
                amount = sum(payslip.input_line_ids.filtered(lambda x: x.code == rule_code).mapped('amount'))
            return amount

    def get_base_salary(self, payslip_id):
        for record in self:
            amount = 0
            payslip = self.env['hr.payslip'].sudo().browse(payslip_id)
            if payslip:
                if record.salary_type == 'manual':
                    # amount = record.wage
                    
                    # wage_b1 = record.wage_history_ids.filtered(lambda x: x.applied_date >= payslip.date_from).sorted(key=lambda x:x.applied_date, reverse=False)
                    # wage_b1 = wage_b1[0].wage if wage_b1 else 0
                    # wage_b2 = record.wage_history_ids.filtered(lambda x: x.applied_date <= payslip.date_to).sorted(key=lambda x:x.applied_date, reverse=True)
                    # wage_b2 = wage_b2[0].wage if wage_b2 else 0
                    
                    # amount = (wage_b1 * sum(payslip.worked_days_line_ids.filtered(lambda x: x.code == 'ATTND_1').mapped("number_of_days")) / 30) + (wage_b2 * sum(payslip.worked_days_line_ids.filtered(lambda x: x.code != 'ATTND_1' and 'ATTND_' in x.code).mapped("number_of_days")) / 30)

                    wage_history = record.wage_history_ids.filtered(lambda x: x.applied_date <= payslip.date_to).sorted(key=lambda x:x.applied_date, reverse=True)
                    amount = wage_history[0].wage if wage_history else 0

                elif record.salary_type == 'master':
                    # wage_b1 = record.get_current_umk_amount(record.wage_id.id, payslip.date_from)
                    # wage_b2 = record.get_current_umk_amount(record.wage_id.id, payslip.date_to)
                    # if payslip.worked_days_line_ids:
                    #     amount = (wage_b1 * sum(payslip.worked_days_line_ids.filtered(lambda x: x.code == 'ATTND_1').mapped("number_of_days")) / 30) + (wage_b2 * sum(payslip.worked_days_line_ids.filtered(lambda x: x.code != 'ATTND_1' and 'ATTND_' in x.code).mapped("number_of_days")) / 30)

                    if payslip.date_to.year != payslip.date_from.year:
                        date_from_next_month = payslip.date_from.replace(day=28) + timedelta(days=4)
                        date_fromlast_day_of_month =  date_from_next_month - timedelta(days=date_from_next_month.day)

                        wage_b1 = record.wage_id.umk_history_ids.filtered(lambda x: x.applied_date <= date_fromlast_day_of_month).sorted(key=lambda x:x.applied_date, reverse=True)
                        wage_b1 = wage_b1[0].umk_amount if wage_b1 else 0
                        wage_b2 = record.wage_id.umk_history_ids.filtered(lambda x: x.applied_date <= payslip.date_to).sorted(key=lambda x:x.applied_date, reverse=True)
                        wage_b2 = wage_b2[0].umk_amount if wage_b2 else 0

                        amount = (wage_b1 + wage_b2) / 2
                    else:
                        amount = record.get_current_umk_amount(record.wage_id.id, payslip.date_to)
                        
            return amount

    ####################################
    # Action Button
    ####################################

    def action_update_salary_amount(self):
        for record in self:
            okey = self._context.get('okey',False)
            umk_amount = self._context.get('umk_amount',0)
            applied_date = self._context.get('applied_date',False)

            if not okey:
                context = {
                    'default_umk_amount': record.wage,
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_update_salary_amount",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Update Amount',
                    'res_model':'update.amount.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_payroll.update_amount_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
            record.wage = umk_amount
            record.set_salary_history(umk_amount, applied_date)


class HrContractWageHistory(models.Model):
    _name = 'hr.contract.wage_history'
    _description = "Contract Wage History"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']

    # head
    contract_id = fields.Many2one('hr.contract', string='Contract')

    wage = fields.Float(string='Wage', required=True, tracking=True)
    applied_date = fields.Date(string='Applied Date', required=True, tracking=True)
