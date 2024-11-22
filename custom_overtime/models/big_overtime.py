import time
from datetime import datetime

import json
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import SUPERUSER_ID

# from odoo.osv import osv
import logging 

STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approve1','Approved Manager'),
    ('approve2','Approved HR'),
    ('cancel','Canceled'),
    ('reject','Rejected'),
]
def unique(list1):

    # initialize a null list
    unique_list = []

    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

class big_overtime(models.Model):
    _name = 'big.overtime'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Overtime Management'
    
    name = fields.Char('Name')


    overtime_type = fields.Selection([
        ('pribadi', 'Pribadi'),
        ('kolektif', 'Kolektif'),
    ], string='Type', default='pribadi', required=True, tracking=True)

    @api.onchange('overtime_type')
    def _onchange_overtime_type(self):
        for record in self:
            if record.overtime_type == 'kolektif':
                record.employee_id = False
                record.overtime_date = False
            elif record.overtime_type == 'pribadi':
                record.kolektif_department_id = False
                record.kolektif_section = False
                record.overtime_kolektif_ids = False


    
    # EMP DETAIL
    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True)
    nik = fields.Char(related="employee_id.barcode", string="NIK")
    job_id = fields.Many2one(related='employee_id.job_id', string="Job Position")
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    section = fields.Many2one(related='employee_id.section', string='Section')
    work_location_id = fields.Many2one(related="employee_id.work_location_id", string='Unit')
    is_wonogiri_area = fields.Boolean(related="employee_id.work_location_id.is_wonogiri_area", store=True)
    resource_calendar_id = fields.Many2one(related="employee_id.resource_calendar_id", string='Working Times')
    hari_kerja = fields.Integer(compute='_compute_hari_kerja', string='Hari Kerja', store=True)
    
    @api.depends('employee_id','work_location_id','work_location_id.is_wonogiri_area','employee_id.resource_calendar_id','resource_calendar_id')
    def _compute_hari_kerja(self):
        for record in self:
            hari_kerja = 0

            if record.employee_id.resource_calendar_id:
                list_day_of_week = [x.dayofweek for x in record.employee_id.resource_calendar_id.attendance_ids]
                if list_day_of_week:
                    hari_kerja = len(unique(list_day_of_week))
            
            record.hari_kerja = hari_kerja



    # SP Lembur
    kolektif_department_id = fields.Many2one('hr.department', string='Department')
    kolektif_section = fields.Many2one('hr.department', string='Section')

    @api.onchange('kolektif_department_id','kolektif_section')
    def _onchange_kolektif_department_section(self):
        for record in self:
            if record.kolektif_department_id and record.kolektif_section:
                overtime_kolektif_ids = []
                
                # search employee
                list_emp = self.env['hr.employee'].search([('department_id','=',record.kolektif_department_id.id),('section','=',record.kolektif_section.id)])
                # raise UserError(list_emp)
                for emp in list_emp:
                    overtime_kolektif_ids.append([0,0,{
                        'employee_id':emp.id,
                        'menit_istirahat':record.menit_istirahat,
                        'start_date':record.start_date,
                        'end_date':record.end_date,
                        # 'description':record.description,
                    }])
            
                record.overtime_kolektif_ids = None
                record.overtime_kolektif_ids = overtime_kolektif_ids

    overtime_date = fields.Date(string='Tanggal Lembur', tracking=True)
    jenis_lembur = fields.Selection([
        ('awal', 'Lembur Awal'),
        ('terusan', 'Lembur Terusan'),
        ('libur', 'Lembur Libur'),
    ], string='Jenis Lembur', default="awal", required=True, tracking=True)
    description = fields.Text('Keterangan', required=True, tracking=True)
    

    # Detail Lembur
    @api.onchange('overtime_date')
    def _onchange_overtime_date(self):
        for record in self:
            if record.overtime_date and not (record.start_date and record.end_date):
                record.start_date = datetime.now()
                record.start_date = record.overtime_date
                record.end_date = record.overtime_date

    start_date = fields.Datetime(string='Waktu Start Lembur', tracking=True)
    end_date = fields.Datetime(string='Waktu End Lembur', tracking=True)
    is_shift_malam = fields.Boolean('Shift Malam', tracking=True)

    menit_istirahat = fields.Selection([
        ('15', '15 Menit'),
        ('30', '30 Menit'),
        ('45', '45 Menit'),
        ('60', '60 Menit'),
    ], string='Menit Istirahat')

    overtime_hours = fields.Float(compute='_compute_overtime_hours', string='Durasi', store=True, tracking=True)

    @api.depends('start_date','end_date', 'menit_istirahat')
    def _compute_overtime_hours(self):
        for record in self:
            overtime_hours = 0
            if record.start_date and record.end_date:
                diff = record.end_date - record.start_date
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                
                minutes_in_hours = minutes/60 if minutes else 0
                overtime_hours = hours + minutes_in_hours

                # menit istirahat
                if record.menit_istirahat and eval(record.menit_istirahat):
                    menit_istirahat = eval(record.menit_istirahat)/60
                    overtime_hours = overtime_hours - menit_istirahat if overtime_hours > 0 else 0

            record.overtime_hours = overtime_hours


    # kolektif
    overtime_kolektif_ids = fields.One2many('big.overtime.kolektif', 'ovr_id', string='Overtime Kolektif')
    @api.onchange('start_date','end_date','menit_istirahat')
    def _onchange_start_end_rest(self):
        for record in self:
            for kol in record.overtime_kolektif_ids:
                kol.start_date = record.start_date
                kol.end_date = record.end_date
                kol.menit_istirahat = record.menit_istirahat

    
    # approval
    @api.onchange(
        'overtime_type',
        'employee_id',
        'kolektif_department_id',
        'kolektif_section',
    )
    def _onchange_overtime_type_approval(self):
        for record in self:
            if record.overtime_type == 'pribadi':
                record.manager_id = record.employee_id.parent_id.id
            elif record.overtime_type == 'kolektif':
                record.manager_id = record.kolektif_department_id.manager_id.id
            
            group_hr = self.env.ref('custom_overtime.ovr_human_resource')
            if group_hr and group_hr.users and group_hr.users[0].employee_id:
                record.hr_responsible_id = group_hr.users[0].employee_id.id 

    manager_id = fields.Many2one('hr.employee', string='Manager', tracking=True)
    hr_responsible_id = fields.Many2one('hr.employee', string='HR Responsible', tracking=True)

    allocation_ids = fields.Many2many('hr.leave.allocation', string='Allocations')
    allocation_count = fields.Integer(compute='_compute_allocation_count', string='Allocation Count')
    
    @api.depends('allocation_ids')
    def _compute_allocation_count(self):
        for record in self:
            record.allocation_count = len(record.allocation_ids) if record.allocation_ids else 0

    # for tree view
    rel_employee_ids = fields.Many2many('hr.employee', compute="_compute_employee_department_list", string='Employee(s)')
    rel_department_id = fields.Many2one('hr.department', compute="_compute_employee_department_list", string='Department')
    rel_section = fields.Many2one('hr.department', compute="_compute_employee_department_list", string='Section')
    
    @api.depends(
        'employee_id',
        'department_id',
        'section',
        'kolektif_department_id',
        'kolektif_section')
    def _compute_employee_department_list(self):
        for record in self:
            rel_employee_ids = []
            rel_department_id = None
            rel_section = None
            if record.employee_id and record.overtime_type == 'pribadi':
                rel_employee_ids.append(record.employee_id.id)
                rel_department_id = record.department_id.id
                rel_section = record.section.id
            if record.overtime_kolektif_ids and record.overtime_type == 'kolektif':
                rel_department_id = record.kolektif_department_id.id
                rel_section = record.kolektif_section.id
                for kol in record.overtime_kolektif_ids:
                    rel_employee_ids.append(kol.employee_id.id)

            record.rel_employee_ids = rel_employee_ids
            record.rel_department_id = rel_department_id
            record.rel_section = rel_section


    approval_ids = fields.One2many('big.overtime.approval.line','ovr_id', string='Approval Line')

    state = fields.Selection(STATE,
        string='State',
        default='draft',
        readonly=True,
        required=True, tracking=True)    

    state_cancel = fields.Selection(related="state", tracking=False)
    state_reject = fields.Selection(related="state", tracking=False)


    # set hour in overtime
    ovr_hour_detail_ids = fields.One2many('big.overtime.hour.detail', 'ovr_id', string='Detail Overtime Hours')

    @api.model
    def create(self, values):
        values['name'] =  self.env['ir.sequence'].get_sequence(self._name, 'OVR')
        res = super(big_overtime,self).create(values)
        return res
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Tidak bisa menghapus data dengan state selain DRAFT!'))
            res = super(big_overtime,self).unlink()
            return res

    def create_timeoff_allocation(self):
        for record in self:
            if not record.is_wonogiri_area:
                leave_type_id = self.env['hr.leave.type'].sudo().search([('name','=','Pulang Cepat')])
                if not leave_type_id:
                    raise UserError("Silahkan buat Leave type dengan nama 'Pulang Cepat' pada Config Timeoff Terlebih dahulu!")
                allocation_ids = []
                
                if record.employee_id:
                    # raise UserError(record.overtime_hours)
                    allocation = self.env['hr.leave.allocation'].sudo().create({
                        'name' : f'Allocation for overtime {record.name}',
                        'holiday_status_id': leave_type_id.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'regular',
                        'date_from': datetime.now().date(),
                        'number_of_hours_display': record.overtime_hours,
                        'employee_id' : record.employee_id.id,
                        'notes': f'This timeoff allocation for this employee is auto generated from Overtime Management module.\n\nsrc: {record.name}'
                    })
                    allocation.sudo().write({'number_of_hours_display' : record.overtime_hours})
                    allocation.sudo().action_confirm()
                    allocation.sudo().action_validate()
                    allocation_ids.append(allocation.id)

                if record.overtime_kolektif_ids:
                    for kol in record.overtime_kolektif_ids.filtered(lambda x: x.employee_id.work_location_id and x.employee_id.work_location_id.is_wonogiri_area):
                        allocation = self.env['hr.leave.allocation'].sudo().create({
                            'name' : f'Allocation for overtime {record.name}',
                            'holiday_status_id': leave_type_id.id,
                            'holiday_type': 'employee',
                            'allocation_type': 'regular',
                            'date_from': datetime.now().date(),
                            'number_of_hours_display': kol.overtime_hours,
                            'employee_id' : kol.employee_id.id,
                            'notes': f'This timeoff allocation for this employee is auto generated from Overtime Management module.\n\nsrc: {record.name}'
                        })
                        allocation.sudo().write({'number_of_hours_display' : kol.overtime_hours})
                        allocation.sudo().action_confirm()
                        allocation.sudo().action_validate()
                        allocation_ids.append(allocation.id)

                record.allocation_ids = allocation_ids
    
    def create_overtime_hour_detail(self):
        for record in self:
            ovr_hour_detail_ids = []
            if record.overtime_type == 'pribadi' and record.employee_id.work_location_id.is_wonogiri_area:
                # perhitungan jenis libur
                if record.jenis_lembur == 'libur':
                    if record.hari_kerja <= 5:
                        # 8 jam pertama
                        name = "Lembur Hari Libur (8 Jam Pertama)"
                        jam_kerja = record.overtime_hours if record.overtime_hours < 8 else 8
                        ovr_hour_detail_ids.append([0,0,{
                            'employee_id':record.employee_id.id,
                            'name':name,
                            'code':"OVR_L1",
                            'number_of_hours':jam_kerja,
                        }])
                        # jam ke 9
                        if record.overtime_hours > 8:
                            name = "Lembur Hari Libur (Jam ke-9)"
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':record.employee_id.id,
                                'name':name,
                                'code':"OVR_L2",
                                'number_of_hours':1,
                            }])
                        # jam ke 10-11
                        if record.overtime_hours > 9:
                            name = "Lembur Hari Libur (Jam ke-10 dst)"
                            jam_kerja = record.overtime_hours - 9
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':record.employee_id.id,
                                'name':name,
                                'code':"OVR_L3",
                                'number_of_hours':jam_kerja,
                            }])
                    # 6 hari kerja ++
                    else:
                        # 7 jam pertama
                        name = "Lembur Hari Libur (7 Jam Pertama)"
                        jam_kerja = record.overtime_hours if record.overtime_hours < 7 else 7
                        ovr_hour_detail_ids.append([0,0,{
                            'employee_id':record.employee_id.id,
                            'name':name,
                            'code':"OVR_L1",
                            'number_of_hours':jam_kerja,
                        }])
                        # jam ke 8
                        if record.overtime_hours > 7:
                            name = "Lembur Hari Libur (Jam ke-8)"
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':record.employee_id.id,
                                'name':name,
                                'code':"OVR_L2",
                                'number_of_hours':1,
                            }])
                        # jam ke 10-11
                        if record.overtime_hours > 8:
                            name = "Lembur Hari Libur (Jam ke-10 dst)"
                            jam_kerja = record.overtime_hours - 8
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':record.employee_id.id,
                                'name':name,
                                'code':"OVR_L3",
                                'number_of_hours':jam_kerja,
                            }])
                
                # perhitungan lembur di hari kerja
                else:
                    # jam pertama
                    name = "Lembur Hari Kerja (Jam Pertama)"
                    jam_kerja = record.overtime_hours if record.overtime_hours < 1 else 1
                    ovr_hour_detail_ids.append([0,0,{
                        'employee_id':record.employee_id.id,
                        'name':name,
                        'code':"OVR_K1",
                        'number_of_hours':jam_kerja,
                    }])
                    # 2 jam berikutnya
                    if record.overtime_hours > 1:
                        name = "Lembur Hari Kerja (2 Jam Berikutnya)"
                        jam_kerja = record.overtime_hours - 1
                        ovr_hour_detail_ids.append([0,0,{
                            'employee_id':record.employee_id.id,
                            'name':name,
                            'code':"OVR_K2",
                            'number_of_hours':jam_kerja,
                        }])
            elif record.overtime_type == 'kolektif':
                if record.jenis_lembur == 'libur':
                    for kol in record.overtime_kolektif_ids.filtered(lambda x : x.employee_id.work_location_id.is_wonogiri_area):
                        if kol.hari_kerja <= 5:
                            # 8 jam pertama
                            name = "Lembur Hari Libur (8 Jam Pertama)"
                            jam_kerja = kol.overtime_hours if kol.overtime_hours < 8 else 8
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':kol.employee_id.id,
                                'name':name,
                                'code':"OVR_L1",
                                'number_of_hours':jam_kerja,
                            }])
                            # jam ke 9
                            if kol.overtime_hours > 8:
                                name = "Lembur Hari Libur (Jam ke-9)"
                                ovr_hour_detail_ids.append([0,0,{
                                    'employee_id':kol.employee_id.id,
                                    'name':name,
                                    'code':"OVR_L2",
                                    'number_of_hours':1,
                                }])
                            # jam ke 10-11
                            if kol.overtime_hours > 9:
                                name = "Lembur Hari Libur (Jam ke-10 dst)"
                                jam_kerja = kol.overtime_hours - 9
                                ovr_hour_detail_ids.append([0,0,{
                                    'employee_id':kol.employee_id.id,
                                    'name':name,
                                    'code':"OVR_L3",
                                    'number_of_hours':jam_kerja,
                                }])
                        # 6 hari kerja ++
                        else:
                            # 7 jam pertama
                            name = "Lembur Hari Libur (7 Jam Pertama)"
                            jam_kerja = kol.overtime_hours if kol.overtime_hours < 7 else 7
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':kol.employee_id.id,
                                'name':name,
                                'code':"OVR_L1",
                                'number_of_hours':jam_kerja,
                            }])
                            # jam ke 8
                            if kol.overtime_hours > 7:
                                name = "Lembur Hari Libur (Jam ke-8)"
                                ovr_hour_detail_ids.append([0,0,{
                                    'employee_id':kol.employee_id.id,
                                    'name':name,
                                    'code':"OVR_L2",
                                    'number_of_hours':1,
                                }])
                            # jam ke 10-11
                            if kol.overtime_hours > 8:
                                name = "Lembur Hari Libur (Jam ke-10 dst)"
                                jam_kerja = kol.overtime_hours - 8
                                ovr_hour_detail_ids.append([0,0,{
                                    'employee_id':kol.employee_id.id,
                                    'name':name,
                                    'code':"OVR_L3",
                                    'number_of_hours':jam_kerja,
                                }])
                
                # perhitungan lembur di hari kerja
                else:
                    for kol in record.overtime_kolektif_ids.filtered(lambda x : x.employee_id.work_location_id.is_wonogiri_area):
                        # jam pertama
                        name = "Lembur Hari Kerja (Jam Pertama)"
                        jam_kerja = kol.overtime_hours if kol.overtime_hours < 1 else 1
                        ovr_hour_detail_ids.append([0,0,{
                            'employee_id':kol.employee_id.id,
                            'name':name,
                            'code':"OVR_K1",
                            'number_of_hours':jam_kerja,
                        }])
                        # 2 jam berikutnya
                        if kol.overtime_hours > 1:
                            name = "Lembur Hari Kerja (2 Jam Berikutnya)"
                            jam_kerja = kol.overtime_hours - 1
                            ovr_hour_detail_ids.append([0,0,{
                                'employee_id':kol.employee_id.id,
                                'name':name,
                                'code':"OVR_K2",
                                'number_of_hours':jam_kerja,
                            }])

            # raise UserError(str(ovr_hour_detail_ids))
            record.ovr_hour_detail_ids = None
            record.ovr_hour_detail_ids = ovr_hour_detail_ids

    @api.constrains('rel_employee_ids','employee_id','overtime_kolektif_ids','overtime_kolektif_ids.employee_id','start_date','end_date')
    def _constrains_employee(self):
        for record in self:
            overtime = self.env['big.overtime'].sudo().search([
                ('id','!=',record.id),
                # ('rel_employee_ids.ids','=', record.rel_employee_ids.ids),
                ('end_date','>=', record.start_date),
                ('start_date','<=', record.end_date),
                ('state','not in',['cancel','reject']),
            ])
            overtime_list = overtime.filtered(lambda x: set(x.rel_employee_ids.ids) & set(record.rel_employee_ids.ids) )
            if overtime_list:
                message = f'This Overtime date is overlapping with other overtime record, check your list employee\n\nsrc : {overtime_list[0].name}'
                raise ValidationError(message)


    ###############################################
    # Button
    ###############################################
    
    # open allocation
    def action_open_allocations(self):
        for record in self:
            if record.allocation_ids:
                if len(record.allocation_ids) == 1:
                    return {
                        'name': _("Allocations"),
                        'type': 'ir.actions.act_window',
                        'res_model': 'hr.leave.allocation',
                        'view_mode': 'form',
                        'res_id': record.allocation_ids[0].id,
                        'context': {'create': False, 'delete': False},
                    }
                else:
                    return {
                        'name': _("Allocations"),
                        'type': 'ir.actions.act_window',
                        'res_model': 'hr.leave.allocation',
                        'view_mode': 'tree,form',
                        # 'res_id': self.order_ids,
                        'domain': [('id', 'in', record.allocation_ids.ids)],
                        'context': {'create': False, 'delete': False},
                    }
            
    # RFA
    def action_rfa(self):
        for record in self:
            # set overtime detail hours
            record.create_overtime_hour_detail()

            record.state = 'rfa'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # create schedule activity 
            if record.manager_id and record.manager_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Overtime number {record.name} need your approval',
                    'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Overtime Management',
                    'date_deadline': datetime.now(),
                    'user_id': record.manager_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('custom_overtime.model_big_overtime').id,
                    'activity_type_id': 4 #to do
                })
    
    # Approve Manager
    def action_approve1(self):
        for record in self:
            record.state = 'approve1'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})
            
            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            # create schedule activity 
            if record.hr_responsible_id and record.hr_responsible_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Overtime number {record.name} need your approval',
                    'summary': f'Dear HR Responsible of {record.employee_id.name}, we need your approval for Overtime Management',
                    'date_deadline': datetime.now(),
                    'user_id': record.hr_responsible_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('custom_overtime.model_big_overtime').id,
                    'activity_type_id': 4 #to do
                })
    
    # Approve HRD
    def action_approve2(self):
        for record in self:
            record.state = 'approve2'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            # create schedule activity 
            # if record.manager_id and record.manager_id.user_id:
            #     self.env['mail.activity'].create({
            #         'note': f'Overtime number {record.name} need your approval',
            #         'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Overtime Management',
            #         'date_deadline': datetime.now(),
            #         'user_id': record.manager_id.user_id.id,
            #         'res_id': record.id,
            #         'res_model_id': self.env.ref('custom_overtime.model_big_overtime').id,
            #         'activity_type_id': 4 #to do
            #     })
                

            # create timeoff allocation
            record.create_timeoff_allocation()

        
    # REVISE
    def action_revise(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_revise",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Revise Wizard',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }

            record.state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': 'revise',
                # 'closing_state': record.closing_state,
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # REJECT
    def action_reject(self):
        for record in self:
            record.state = 'reject'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # Cancel
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

    # Set to Draft
    def action_draft(self):
        for record in self:
            record.state = 'draft'

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

class big_overtime_kolektif(models.Model):
    _name = 'big.overtime.kolektif'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Overtime Management (Kolektif)'
    
    ovr_id = fields.Many2one('big.overtime', string='Overtime', ondelete="cascade")

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    work_location_id = fields.Many2one(related="employee_id.work_location_id", string='Unit')
    is_wonogiri_area = fields.Boolean(related="employee_id.work_location_id.is_wonogiri_area", store=True)
    resource_calendar_id = fields.Many2one(related="employee_id.resource_calendar_id", string='Working Times')
    hari_kerja = fields.Integer(compute='_compute_hari_kerja', string='Hari Kerja', store=True)
    
    @api.depends('employee_id','work_location_id','work_location_id.is_wonogiri_area','employee_id.resource_calendar_id','resource_calendar_id')
    def _compute_hari_kerja(self):
        for record in self:
            hari_kerja = 0

            if record.employee_id.resource_calendar_id:
                list_day_of_week = [x.dayofweek for x in record.employee_id.resource_calendar_id.attendance_ids]
                if list_day_of_week:
                    hari_kerja = len(unique(list_day_of_week))
            
            record.hari_kerja = hari_kerja

    menit_istirahat = fields.Selection([
        ('15', '15 Menit'),
        ('30', '30 Menit'),
        ('45', '45 Menit'),
        ('60', '60 Menit'),
    ], string='Menit Istirahat')
    start_date = fields.Datetime(string='Start Lembur', required=True, tracking=True)
    end_date = fields.Datetime(string='End Lembur', required=True, tracking=True)
    overtime_hours = fields.Float(compute='_compute_overtime_hours', string='Durasi', store=True, tracking=True)

    @api.depends('start_date','end_date', 'menit_istirahat')
    def _compute_overtime_hours(self):
        for record in self:
            overtime_hours = 0
            if record.start_date and record.end_date:
                diff = record.end_date - record.start_date
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                
                minutes_in_hours = minutes/60 if minutes else 0
                overtime_hours = hours + minutes_in_hours

                # menit istirahat
                if record.menit_istirahat and eval(record.menit_istirahat):
                    menit_istirahat = eval(record.menit_istirahat)/60
                    overtime_hours = overtime_hours - menit_istirahat if overtime_hours > 0 else 0

            record.overtime_hours = overtime_hours

    description = fields.Text('Keterangan', tracking=True)


class big_overtime_hour_detail(models.Model):
    _name = 'big.overtime.hour.detail'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Overtime Management (Detailed Hour)'

    ovr_id = fields.Many2one('big.overtime', string='Overtime', ondelete="cascade")
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    name = fields.Char(string='Description', required=True)
    code = fields.Char(string='Code', required=True)
    number_of_hours = fields.Float(string='Duration', required=True)


# approval
class big_overtime_approval_line(models.Model):
    _name = "big.overtime.approval.line"
    _description = 'Overtime Management (Approval Line)'

    ovr_id = fields.Many2one('big.overtime', string='Overtime', ondelete="cascade")

    state = fields.Selection(STATE + [('revise','Revise')], string='State')    
    
    reason = fields.Text('Reason')

    pelaksana_id = fields.Many2one('res.users','Pelaksana', size=128)
    department_id = fields.Many2one(related='pelaksana_id.employee_id.department_id', string="Department")
    job_id = fields.Many2one(related='pelaksana_id.employee_id.job_id', string="Position")

    tanggal = fields.Datetime('Tanggal')