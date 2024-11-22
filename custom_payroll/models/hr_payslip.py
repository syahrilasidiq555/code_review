# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    date_start = fields.Date(default=lambda self: fields.Date.to_string((date.today() + relativedelta(months=-1)).replace(day=16)))
    date_end = fields.Date(default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date().replace(day=15)))
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_worker_payslip = fields.Boolean(string='Is Worker Payslip')
    is_gaji_probation = fields.Boolean(compute='_compute_is_gaji_probation', string='is Gaji 3 Bulan Awal', store=True)
    
    @api.depends('date_to','employee_id','employee_id.join_date','employee_id.job_id','employee_id.job_id.is_admin_level')
    def _compute_is_gaji_probation(self):
        for record in self:
            record.is_gaji_probation = False
            if record.employee_id and record.employee_id.join_date and record.employee_id.job_id and record.employee_id.job_id.is_admin_level:
                join_date_gap = record.employee_id.join_date.replace(day=1) + relativedelta(months=3, days=-1)
                if record.date_to <= join_date_gap:
                    record.is_gaji_probation = True

            if record.employee_id.job_id and record.employee_id.job_id.is_worker_level:
                record.is_worker_payslip = True


    date_from = fields.Date(default=lambda self: fields.Date.to_string((date.today() + relativedelta(months=-1)).replace(day=16)))
    date_to = fields.Date(default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date().replace(day=15)))

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        def myFunc(e):
            return e['name']

        res =  super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

        for contract in contracts:
            # get salary correction input
            corrections = self.env['hr.payslip.correction.detail'].sudo().search([
                ('correction_id.employee_id','=',contract.employee_id.id),
                ('correction_id.state','=','confirm'),
                # ('due_date','>=',day_from.date()),
                ('due_date','<=',day_to.date()),
                ('is_pay','=',False),
            ])
            if corrections:
                list_id = []
                for correction in corrections:
                    if correction.id in list_id:
                        continue
                    res.append({
                        'name': f"({correction.correction_id.name}) {correction.description}",
                        'sequence': 10,
                        'code': correction.correction_id.salary_rule_id.code,
                        'amount': correction.amount,
                        'contract_id': contract.id,
                        'is_correction': True,
                        'correction_checklist': True,
                        'correction_detail_id': correction.id,
                    })
                    list_id.append(correction.id)
                    other_correction = self.env['hr.payslip.correction.detail'].sudo().search([
                        ('correction_id','=',correction.correction_id.id),
                        ('id','not in', list_id),
                        ('is_pay','=',False),
                    ])
                    for other in other_correction.filtered(lambda x: x.id not in list_id):
                        res.append({
                            'name': f"({other.correction_id.name}) {other.description}",
                            'sequence': 10,
                            'code': other.correction_id.salary_rule_id.code,
                            'amount': other.amount,
                            'contract_id': contract.id,
                            'is_correction': True,
                            'correction_checklist': other.due_date <= correction.due_date,
                            'correction_detail_id': other.id,
                        })
                        list_id.append(other.id)
                res.sort(key=myFunc)
        return res

    
    # @api.model
    # def get_worked_day_lines(self, contracts, date_from, date_to):
    #     res =  super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
    #     day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
    #     day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
        
    #     for contract in contracts:
    #         # GET PEMOTONG INSENTIF ATTENDANCE LEAVE
    #         pass
            
    #     return res
    
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res =  super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

        for contract in contracts:
            # GET PEMOTONG INSENTIF ATTENDANCE LEAVE DAN PEMOTONG BASE SALARY
            number_of_days = 0
            number_of_hours = 0
            bs_number_of_days = 0
            bs_number_of_hours = 0
            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                # PEMOTONG INSENTIF ATTENDANCE
                if holiday.holiday_status_id.is_affect_attendance_incentive:
                    number_of_hours -= hours
                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        number_of_days -= hours / work_hours
                
                # PEMOTONG BASE SALARY
                if holiday.holiday_status_id.is_affect_base_salary:
                    bs_number_of_hours -= hours
                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        bs_number_of_days -= hours / work_hours


            if number_of_days:
                res.append({
                    'name': "Leaves that cut attendance incentives",
                    'sequence': 2,
                    'code': 'ATT_INC_CUT',
                    'number_of_days': number_of_days,
                    'number_of_hours': number_of_hours,
                    'contract_id': contract.id,
                })
                
            if bs_number_of_days:
                res.append({
                    'name': "Leaves that cut Base Salary",
                    'sequence': 2,
                    'code': 'BS_CUT',
                    'number_of_days': bs_number_of_days,
                    'number_of_hours': bs_number_of_hours,
                    'contract_id': contract.id,
                })
        return res

    def update_status_correction(self):
        for correction in self.input_line_ids:
            if correction.is_correction and correction.correction_checklist:
                correction.correction_detail_id.sudo().write({'is_pay': True})

    def reverse_status_correction(self):
        for correction in self.input_line_ids:
            if correction.is_correction and correction.correction_checklist:
                correction.correction_detail_id.sudo().write({'is_pay': False})

    def action_payslip_done(self):
        self.compute_sheet()
        self.update_status_correction()
        return self.write({'state': 'done'})

    def unlink(self):
        for rec in self:
            rec.reverse_status_correction()
        return super(HrPayslip, self).unlink()

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    correction_checklist = fields.Boolean(default=False, string="Correction")
    is_correction = fields.Boolean(default=False)
    correction_detail_id = fields.Many2one('hr.payslip.correction.detail')