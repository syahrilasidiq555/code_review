import time
from datetime import datetime, timedelta, date

# import json
from lxml import etree


import psycopg2
import psycopg2.extras

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

import logging 

class dym_teguran_attendance(models.Model):
    _name = 'dym.teguran.attendance'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Teguran Attendance"
    
    STATE_SELECTION = [
        ('confirmed','Confirmed'),
        ('approved', 'Approved HRD'),
        ('refuse', 'Refused')
    ]

    name = fields.Char('Teguran Name')
    employee_id = fields.Many2one('hr.employee',string='Nama Karyawan', required=True)    
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    nik = fields.Char(related='employee_id.barcode',string='NIK')
    
    # teguran_tipe = fields.Selection(
    #     [('terlambat','Terlambat'),
    #     ('out_of_range','Out of Range')],
    #     string='Tipe Teguran',
    #     required=True
    # )
    reason = fields.Char(string='Alasan', required=True)

    # Attendance line
    # attendance_lines = fields.One2many('dym.teguran.attendance.line','teguran_id', string='Attendance List', ondelete='cascade')
    attendance_lines = fields.Many2many('hr.attendance','hr_attendance_teguran_rel','teguran_id','attendance_id', string='Attendance List')

    # Approval
    approval_ids = fields.One2many('dym.teguran.attendance.approval.line', 'transaction_id', string="Table Approval", ondelete='cascade')
    # State Workflow
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='confirmed')
    state_refuse = fields.Selection(related='state')


    
    # DIJALANIN SEBULAN SEKALI
    def cron_create_teguran_attendance(self):
        date_now = datetime.now() + timedelta(hours=7)
        # date_now = datetime.now() + timedelta(hours=7)
        date_start = date_now.replace(day=1,minute=0,hour=0,second=0,microsecond=0)
        next_month = date_start.replace(day=28) + timedelta(days=4)
        date_end = next_month - timedelta(days=next_month.day)
        date_end = date_end.replace(minute=59,hour=23,second=59,microsecond=59)

        employee_ids = self.env['hr.employee'].search([('active','=','t'),('barcode','!=','')])

        for employee_id in employee_ids:
            
            # TERLAMBAT 4 Kali dalam 1 Bulan
            query_cek_terlambat = f"""
                select
                    distinct on (date(check_in+'7 hours'::interval))
                    id,
                    employee_id,
                    check_in+'7 hours'::interval as check_in
                from hr_attendance
                where terlambat = 't'
                and check_in+'7 hours'::interval >= '{date_start}' and check_in+'7 hours'::interval <= '{date_end}'
                --untuk validasi jika tidak ingin double
                --and id not in (select attendance_id from hr_attendance_teguran_rel)
                and employee_id = {employee_id.id}

                order by date(check_in+'7 hours'::interval), check_in asc
            """
            self._cr.execute(query_cek_terlambat)
            # raise ValidationError('data : '+str(query_cek_terlambat))
            all_lines = self._cr.dictfetchall()

            if all_lines:
                if len(all_lines) >= 4:
                    # create teguran
                    attendance_lines = []
                    for line in all_lines:
                        attendance_lines.append((4,line['id']))
                        if len(attendance_lines) == 4:
                            break
                    data_terlambat = {
                        'employee_id':employee_id.id,
                        # 'teguran_tipe':'terlambat',
                        'reason':'Terlambat lebih dari 4 kali dalam 1 bulan yg sama',
                        'attendance_lines':attendance_lines,
                        'state':'confirmed'
                    }
                    teguran_id = self.env['dym.teguran.attendance'].create(data_terlambat)
                
                if len(all_lines) >= 6:
                    # create teguran
                    attendance_lines = []
                    for line in all_lines:
                        attendance_lines.append((4,line['id']))
                        if len(attendance_lines) == 6:
                            break
                    data_terlambat = {
                        'employee_id':employee_id.id,
                        # 'teguran_tipe':'terlambat',
                        'reason':'Terlambat lebih dari 6 kali dalam 1 bulan yg sama',
                        'attendance_lines':attendance_lines,
                        'state':'confirmed'
                    }
                    teguran_id = self.env['dym.teguran.attendance'].create(data_terlambat)
                
                if len(all_lines) >= 8:
                    # create teguran
                    attendance_lines = []
                    for line in all_lines:
                        attendance_lines.append((4,line['id']))
                        if len(attendance_lines) == 8:
                            break
                    data_terlambat = {
                        'employee_id':employee_id.id,
                        # 'teguran_tipe':'terlambat',
                        'reason':'Terlambat lebih dari 8 kali dalam 1 bulan yg sama',
                        'attendance_lines':attendance_lines,
                        'state':'confirmed'
                    }
                    teguran_id = self.env['dym.teguran.attendance'].create(data_terlambat)
            


            # # TERLAMBAT 3 KALI BERTURUT2 Lintas Bulan
            # date_start2 = date_start - timedelta(days=2)
            # date_end2 = date_end + timedelta(days=2)
            # max_terlambat = 3
            # query_cek_terlambat = """
            #     select
            #         distinct on (date(check_in+'7 hours'::interval))
            #         id,
            #         employee_id,
            #         check_in+'7 hours'::interval
            #     from hr_attendance
            #     where terlambat = 't'
            #     and check_in+'7 hours'::interval >= '"""+str(date_start2)+"""' and check_in+'7 hours'::interval <= '"""+str(date_end2)+"""'
            #     and employee_id = """+str(employee_id.id)+"""

            #     order by date(check_in+'7 hours'::interval), check_in asc
            # """
            # self._cr.execute(query_cek_terlambat)
            # # raise osv.except_osv(_('Warning!'),_('data : '+str(query)))
            # all_lines = self._cr.dictfetchall()
            
            # terlambat_ids = []
            # if all_lines:
            #     if len(all_lines) >= max_terlambat:
            #         count = 0
            #         for i in range(len(all_lines)):
            #             if i != 0:
            #                 attendance_before = self.env['hr.attendance'].search([('id','=',int(all_lines[i-1]['id']))])
            #                 attenadance_now = self.env['hr.attendance'].search([('id','=',int(all_lines[i]['id']))])
            #                 selisih = attenadance_now.check_in.date() - attendance_before.check_in.date()
                            
            #                 if len(terlambat_ids) == max_terlambat:
            #                     break
            #                 if selisih.days == 1:
            #                     count += 1
            #                     if not attendance_before.id in terlambat_ids:
            #                         terlambat_ids.append(attendance_before.id)
            #                     terlambat_ids.append(attenadance_now.id)
                            
            #                 elif selisih.days > 1:
            #                     terlambat_ids = []

            #         # create teguran
            #         attendance_lines = []
            #         if len(terlambat_ids) == max_terlambat:
            #             for line in terlambat_ids:
            #                 # attendance_lines.append([0,0,{
            #                 #     'attendance_id':line
            #                 # }])
            #                 attendance_lines.append((4,line))
            #             data_terlambat = {
            #                     'employee_id':employee_id.id,
            #                     'teguran_tipe':'terlambat',
            #                     'reason':'Terlambat 3 Kali Berturut-turut atau Lebih Lintas Bulan',
            #                     'attendance_lines':attendance_lines,
            #                     'state':'confirmed'
            #                 }
            #             # raise osv.except_osv(_('Warning!'),_('data : '+str(data_terlambat)))
                        
            #             teguran_id = self.env['dym.teguran.attendance'].sudo().create(data_terlambat)
                        


    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get_sequence(self._name, 'STA')
        
        res = super(dym_teguran_attendance,self).create(values)
        return res


    def btn_approve(self):
        for record in self:
            if record.state != 'confirmed':
                raise Warning('Tidak bisa Approve data dengan state selain Confirm !')
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                            'state':'approved',
                            'approval_id':self.env.user.employee_id.id,
                        }])
            record.write({'state':'approved', 'approval_ids':approval_line_ids})

    def btn_refuse(self):
        for record in self:
            if record.state != 'confirmed':
                raise Warning('Tidak bisa Refuse data dengan state selain Confirm !')
            approval_line_ids = []
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                            'state':'refuse',
                            'approval_id':self.env.user.employee_id.id,
                        }])
            record.write({'state':'refuse', 'approval_ids':approval_line_ids}) 


    def print_teguran(self):
        data = {
            'model_id': self.id,
        }
        return self.env.ref('dym_teguran_attendance.print_teguran_attendance').report_action(self, data=data)


# class dym_teguran_attendance_line(models.Model):
#     _name = 'dym.teguran.attendance.line'
#     _description = 'Teguran Attendance Line'

#     teguran_id = fields.Many2one('dym.teguran.attendance',string='Teguran Attendance')
#     # rel_teguran_tipe = fields.Selection(related='teguran_id.teguran_tipe',string='tipe teguran')
#     attendance_id = fields.Many2one('hr.attendance',string='Attendance')
#     check_in = fields.Datetime(related='attendance_id.check_in', string='Check In')
#     outside_range = fields.Boolean(related='attendance_id.outside_range', string='Outsite Range Check In')
#     check_out = fields.Datetime(related='attendance_id.check_out', string='Check Out')
#     outside_range_checkout = fields.Boolean(related='attendance_id.outside_range_checkout', string='Outsite Range Check Out')
#     terlambat = fields.Boolean(related='attendance_id.check_in_terlambat', string='Terlambat')
#     out_of_range_approval = fields.Selection(related='attendance_id.out_of_range_approval', string='Out of Range Check In Approval')
#     oor_approval_co = fields.Selection(related='attendance_id.oor_approval_co', string='Out of Range Check Out Approval')
#     # check_out_terlambat_approval = fields.Selection(related='attendance_id.check_out_terlambat_approval', string='Terlambat Approval')


# Page Approval
class dym_teguran_attendance_approval_line(models.Model):
    _name = "dym.teguran.attendance.approval.line"
    _description = 'Teguran Attendance Line (approval)'

    transaction_id = fields.Many2one('dym.teguran.attendance','Transaction',readonly=True)
    job_id = fields.Many2one(related='approval_id.job_id',string='Position',readonly=True)
    group_id = fields.Many2one('res.groups','Group')
    state = fields.Selection([('approved','Approved HRD'),('refuse','Refused')],readonly=True)
    sequence = fields.Integer('Sequence',readonly=True)
    reason = fields.Char('Reason')
    approval_id = fields.Many2one('hr.employee','Approval',readonly=True)