# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res =  super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

        for contract in contracts:
            pkwt = self.env['hr.kompensasi.pkwt'].search([
                ('employee_id','=',contract.employee_id.id),
            ], order="id desc", limit=1)
            if pkwt:
                res.append({
                    'name': f"({pkwt[0].name}) Kompensasi PKWT",
                    'sequence': 1,
                    'code': "PKWT",
                    'amount': pkwt[0].amount_kompensasi,
                    'contract_id': contract.id,
                })
        return res
    

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res =  super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
        
        for contract in contracts:
            # Get Attendance
            # attendances = self.env['hr.attendance'].search([
            #     ('employee_id','=',contract.employee_id.id),
            #     ('check_out','>=', day_from),
            #     ('check_in','<=', day_to),
            # ])

            # GET ALL ATTENDANCE
            attendance_grouped = self.env['hr.attendance'].sudo().read_group([
                    ('employee_id','=',contract.employee_id.id),
                    ('check_out','>=', day_from),
                    ('check_in','<=', day_to),
                    # ('resource_calendar_id.is_shift_3','=',False),
                ], fields=[
                    'employee_id','check_in','check_out','worked_hours'
                ],groupby=[
                    'check_in:month' ,
                ],
                lazy=False,)
            i = 1
            z = 1
            for attendance in attendance_grouped:
                attendances = self.env['hr.attendance'].sudo().search(attendance['__domain'])
                
                normal_attendances = attendances.filtered(lambda x: not x.resource_calendar_id or (x.resource_calendar_id and not x.resource_calendar_id.is_shift_3))
                shift3_attendances = attendances.filtered(lambda x: x.resource_calendar_id and x.resource_calendar_id.is_shift_3)
                
                # INSERT NORMAL ATTENDANCE
                if normal_attendances:
                    res.append({
                        'name': f"Work Attendances in {attendance['check_in:month']}",
                        'sequence': 6,
                        'code': f"ATTND_{str(i)}",
                        # 'code': f"ATTND",
                        'number_of_days': len(normal_attendances) if normal_attendances else 0,
                        'number_of_hours': sum(normal_attendances.mapped('worked_hours')) if normal_attendances else 0,
                        'contract_id': contract.id,
                    })
                i += 1

                # INSERT SHIFT3 ATTENDANCE
                if shift3_attendances:
                    res.append({
                        'name': f"Work Attendances (SHIFT3) in {attendance['check_in:month']}",
                        'sequence': 7,
                        'code': f"SHIFT3_{str(z)}",
                        # 'code': f"ATTND",
                        'number_of_days': len(shift3_attendances) if shift3_attendances else 0,
                        'number_of_hours': sum(shift3_attendances.mapped('worked_hours')) if shift3_attendances else 0,
                        'contract_id': contract.id,
                    })
                z += 1
            
        return res