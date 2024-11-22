# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res =  super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
        
        for contract in contracts:
            # Get Overtime
            if contract.employee_id.work_location_id.is_wonogiri_area:
                overtime_detail = self.env['big.overtime.hour.detail'].search([
                    ('employee_id','=',contract.employee_id.id),
                    ('ovr_id.overtime_date','>=', day_from),
                    ('ovr_id.overtime_date','<=', day_to),
                    ('ovr_id.state','=', 'approve2'),
                ])
                if overtime_detail:
                    ids = [x.id for x in overtime_detail]
                    query = f'''
                        select 
                            employee_id,
                            name as name,
                            code as code,
                            -- sum(number_of_hours) as number_of_hours
                            floor(sum(number_of_hours)) as number_of_hours
                        from big_overtime_hour_detail
                        where id in {tuple(ids)}
                        group by employee_id,name,code
                        order by employee_id,code
                    '''
                    self.env.cr.execute(query)
                    datas = self.env.cr.dictfetchall()
                    for data in datas:
                        res.append({
                            'name': data['name'],
                            'sequence': 10,
                            'code': data['code'],
                            'number_of_days': None,
                            'number_of_hours': data['number_of_hours'],
                            'contract_id': contract.id,
                        })
        return res