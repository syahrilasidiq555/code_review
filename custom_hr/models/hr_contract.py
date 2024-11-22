from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    is_generate_pkwt = fields.Boolean('Is Generate PKWT ?', default=False)
    


    def get_overtime(self, payslip_id):
        for record in self:
            # gaji = record.contract.wage
            overtime = 0
            # get payslip obj
            payslip = self.env['hr.payslip'].browse(payslip_id)
            if payslip:
                # get worked days
                for work in payslip.worked_days_line_ids.filtered(lambda x : 'OVR' in x.code):
                    # HARI LIBUR
                    if work.code == 'OVR_L1':
                        overtime += work.number_of_hours * 2 * 1/173 * record.wage
                    if work.code == 'OVR_L2':
                        overtime += work.number_of_hours * 3 * 1/173 * record.wage
                    if work.code == 'OVR_L3':
                        overtime += work.number_of_hours * 4 * 1/173 * record.wage
                    # HARI KERJA
                    if work.code == 'OVR_K1':
                        overtime += work.number_of_hours * 1.5 * 1/173 * record.wage
                    if work.code == 'OVR_K2':
                        overtime += work.number_of_hours * 2 * 1/173 * record.wage
            return round(overtime,0)