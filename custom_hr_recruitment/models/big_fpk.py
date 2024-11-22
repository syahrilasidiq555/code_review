import time
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo import SUPERUSER_ID

import json


# from odoo.osv import osv
import logging 

STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approved', 'Approved'),
    ('done', 'Done'),
    ('fulfilled', 'Fulfilled'),
    ('cancel','Canceled'),
    ('reject','Rejected'),
]

JENIS_FPK = [
    ('penggantian_karyawan', 'Penggantian Karyawan'),
    ('penambahan_karyawan', 'Penambahan Karyawan'),
    ('penambahan_jabatan_baru', 'Penambahan Jabatan Baru'),
]

class big_fpk(models.Model):
    _name = 'big.fpk'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Permintaan Karyawan'
    
    name = fields.Char('Name',)


    jenis_fpk = fields.Selection(JENIS_FPK, string='Jenis FPK', required=True)

    @api.onchange('jenis_fpk')
    def _onchange_jenis_fpk(self):
        for record in self:
            if record.jenis_fpk == 'penambahan_jabatan_baru':
                record.job_id = False
                record.penggantian_karyawan_ids = False
            elif record.jenis_fpk == 'penambahan_karyawan':
                record.job_name = False
                record.penggantian_karyawan_ids = False
            elif record.jenis_fpk == 'penggantian_karyawan':
                record.job_name = False

    @api.onchange('jenis_fpk','department_id','job_id')
    def _onchange_jenis_fpk_department(self):
        for record in self:
            record.get_matrix_approval()


    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True)
    section = fields.Many2one('hr.department', string="Section", tracking=True)
    
    # penggantian & penambahan karyawan
    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True)
    # jobdesk = fields.Text('Uraian Job Desk', tracking=True)

    def _get_default_jobdesk(self):
        default_description = self.env.ref("custom_hr_recruitment.default_website_description", raise_if_not_found=False)
        return (default_description._render() if default_description else "")
    
    jobdesk = fields.Html(translate=html_translate, sanitize_attributes=False, default=_get_default_jobdesk, prefetch=False, sanitize_form=False)
    
    # penggantian karyawan
    penggantian_karyawan_ids = fields.One2many('big.fpk.penggantian.list', 'fpk_id', string='List Penggantian Karyawan')
    @api.constrains('penggantian_karyawan_ids')
    def _constrains_penggantian_karyawan_ids(self):
        for record in self:
            if record.jenis_fpk == 'penggantian_karyawan' and not len(record.penggantian_karyawan_ids):
                raise ValidationError("Anda diharuskan mengisi field Alasan Penggantian beserta data list karyawan")

    # penambahan jabatan
    job_name = fields.Char(string='Job Position', tracking=True)
    reason_jabatan = fields.Text('Alasan penambahan jabatan', tracking=True)
    lampiran_list = fields.Many2many('ir.attachment', string='Lampiran')
    # skill_keahlian = fields.Text('Skill / Keahlian')

    
    skill_keahlian = fields.Html(translate=html_translate, sanitize_attributes=False, default=_get_default_jobdesk, prefetch=False, sanitize_form=False)



    jenis_kelamin = fields.Selection([
        ('laki_laki', 'Laki-Laki'),
        ('perempuan', 'Perempaun'),
    ], string='Jenis Kelamin', required=True, tracking=True)
    jumlah_orang = fields.Integer('Jumlah', default=1, required=True, tracking=True)
    @api.constrains('jumlah_orang')
    def _constrains_jumlah_orang(self):
        for record in self:
            if record.jumlah_orang < 1:
                raise ValidationError("Jumlah orang minimal 1!")

    pendidikan_ids = fields.One2many('big.fpk.pendidikan', 'fpk_id', string='Pendidikan')
    @api.constrains('pendidikan_ids')
    def _constrains_pendidikan_ids(self):
        for record in self:
            if len(record.pendidikan_ids) == 0:
                raise ValidationError("Anda harus mengisi detail pendidikan terlebih dahulu!")

    pengalaman_kerja = fields.Selection([
        ('0-1', '0-1 Tahun'),
        ('2-3', '2-3 Tahun'),
        ('3-5', '3-5 Tahun'),
        ('>5', '>5 Tahun'),
    ], string='Pengalaman kerja', required=True, tracking=True)

    karyawan_status = fields.Selection([
        ('kontrak', 'Kontrak'),
        ('percobaan', 'Percobaan'),
    ], string='Karyawan Status', required=True, tracking=True)
    karyawan_durasi = fields.Integer(string='Durasi', required=True, tracking=True)
    karyawan_durasi_uom = fields.Selection([
        ('bulan', 'Bulan'),
        ('tahun', 'Tahun'),
    ], string='Durasi UOM', default='tahun', required=True, tracking=True)



    # approval
    # approval line
    matrix_approval_id = fields.Many2one('big.fpk.matrix.approval', string='Matrix Approval')

    # approval responsible group
    responsible_id = fields.Many2one('big.fpk.matrix.approval.line', string='Approval Stage', readonly=True)

    approval_ids = fields.One2many('big.fpk.approval.line','fpk_id', string="Approval")




    state = fields.Selection(STATE, default='draft', string='State', required=True, readonly=True, tracking=True)
    state_cancel = fields.Selection(related="state", tracking=False)
    state_reject = fields.Selection(related="state", tracking=False)



    @api.model
    def create(self, values):
        res = super(big_fpk,self).create(values)
        suffix  = ''
        if res.jenis_fpk == 'penggantian_karyawan':
            suffix = '/PPK-1/HRD-RECRUITMENT'
        elif res.jenis_fpk == 'penambahan_karyawan':
            suffix = '/PPK-2/HRD-RECRUITMENT'
        elif res.jenis_fpk == 'penambahan_jabatan_baru':
            suffix = '/PJB-2/HRD-RECRUITMENT'
        
        if suffix:
            res.name =  f"No.{self.env['ir.sequence'].get_sequence_fpk(self._name, suffix)}"

        return res
    
    @api.model
    def default_get(self, fields_list):
        res = super(big_fpk, self).default_get(fields_list)
        pendidikan_ids = [
            (0, 0, {'pendidikan': 'SD', 'jurusan': '', }),
            (0, 0, {'pendidikan': 'SMP', 'jurusan': '', }),
            (0, 0, {'pendidikan': 'SMA', 'jurusan': '', }),
            (0, 0, {'pendidikan': 'S1', 'jurusan': '', }),
            (0, 0, {'pendidikan': 'S2', 'jurusan': '', }),
            (0, 0, {'pendidikan': 'S3', 'jurusan': '', }),
        ]

        res.update({
            'pendidikan_ids': pendidikan_ids,
        })
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError('Tidak bisa menghapus data selain Draft !')
        return super(big_fpk, self).unlink()
    

    def get_matrix_approval(self):
        for record in self:
            record.matrix_approval_id = False
            if record.jenis_fpk and record.department_id:
                # get marix approval
                matrix_obj = self.env['big.fpk.matrix.approval']
                domain = [
                    ('jenis_fpk','=',record.jenis_fpk),
                    ('department_ids','=',record.department_id.id),
                    ('active','=',True),
                ]
                if record.jenis_fpk in ['penggantian_karyawan','penambahan_karyawan'] and record.job_id:
                    domain.append(('job_ids','=',record.job_id.id))

                matrix = matrix_obj.search(domain)
                if matrix:
                    record.matrix_approval_id = matrix[0].id
                else:
                    domain = [
                        ('jenis_fpk','=',record.jenis_fpk),
                        ('department_ids','=',record.department_id.id),
                        ('job_ids','=',False),
                        ('active','=',True),
                    ]
                    matrix = matrix_obj.search(domain)
                    if matrix:
                        record.matrix_approval_id = matrix[0].id
                    else:
                        warning_msg = "Matrix Approval pada Department dan Job Position Berikut Tidak Tersedia, Silahkan Hubungi HRD!" 
                        raise ValidationError(warning_msg)


    def validate_user_recipent(self, responsible_group):
        for record in self:
            responsible_employee_id = []
            group_fpk_head = self.env.ref('custom_hr_recruitment.fpk_head')
            group_fpk_manager = self.env.ref('custom_hr_recruitment.fpk_manager')
            group_fpk_hr1 = self.env.ref('custom_hr_recruitment.fpk_hr1')
            group_fpk_hr2 = self.env.ref('custom_hr_recruitment.fpk_hr2')
            group_fpk_direksi = self.env.ref('custom_hr_recruitment.fpk_direksi')
            if record.responsible_id:
                if group_fpk_head.id == responsible_group.id:
                    # GET SPV or Section Head
                    # responsible_employee_id = record.employee_id.department_id.manager_id
                    # pass
                    if record.job_id.superviser_id:
                        responsible_employee_id.append(record.job_id.superviser_id)

                elif group_fpk_manager.id == responsible_group.id:
                    # GET MANAGER OF DEPARTMENT
                    if record.department_id.manager_id:
                        responsible_employee_id.append(record.department_id.manager_id)

                elif group_fpk_hr1.id == responsible_group.id:
                    # GET HR 1
                    if record.responsible_id.employee_ids:
                        for emp in record.responsible_id.employee_ids:
                            responsible_employee_id.append(emp)
                    # else:
                    #     dept = self.env['hr.department'].search([('is_bod','=',True)], limit=1, order="id asc")
                    #     if dept:
                    #         responsible_employee_id.append(dept[0].manager_id)

                elif group_fpk_hr2.id == responsible_group.id:
                    # GET HR 2
                    if record.responsible_id.employee_ids:
                        for emp in record.responsible_id.employee_ids:
                            responsible_employee_id.append(emp)
                    # else:
                    #     dept = self.env['hr.department'].search([('is_bod','=',True)], limit=1, order="id asc")
                    #     if dept:
                    #         responsible_employee_id.append(dept[0].manager_id)
                            
                elif group_fpk_direksi.id == responsible_group.id:
                    # GET DIREKSI
                    if record.responsible_id.employee_ids:
                        for emp in record.responsible_id.employee_ids:
                            responsible_employee_id.append(emp)
                    else:
                        dept = self.env['hr.department'].search([('is_bod','=',True)], limit=1, order="id asc")
                        if dept:
                            responsible_employee_id.append(dept[0].manager_id)

            return responsible_employee_id


    def validate_approval(self):
        for record in self:
            # cek apaakah termasuk group responsible
            if not self.env.user.has_group("custom_hr_recruitment.fpk_superadmin"):
                groups = self.env['res.groups'].search([('id','=',record.responsible_id.group_id.id),('users','=',self.env.user.id)])
                if record.responsible_id.employee_ids:
                    if not self.env.user.employee_id.id in record.responsible_id.employee_ids.ids or not groups:
                        if not self.env.user.employee_id.id in record.responsible_id.employee_ids.ids:
                            list_user = ""
                            for employee in record.responsible_id.employee_ids:
                                list_user += "- "+str(employee.name) + "\n"
                            raise UserError(f'Tidak bisa approve, Anda tidak termasuk Specific User Responsible dalam group {record.responsible_id.group_id.name}. Current Responsible :\n\n{list_user}')
                        elif not groups:
                            raise UserError(f'Tidak bisa approve, Anda tidak termasuk kedalam group {record.responsible_id.group_id.name}.')
                else:
                    if not groups:
                        raise UserError(f'Tidak bisa approve, Anda tidak termasuk kedalam group {record.responsible_id.group_id.name}.')


    def finalize_fpk(self):
        for record in self:
            # create job position and open recruitment
            if record.jenis_fpk == 'penambahan_jabatan_baru':
                job_id = self.env['hr.job'].sudo().create({
                    'name': record.job_name,
                    'department_id': record.department_id.id,
                    'website_published':True,
                    'website_description':record.skill_keahlian,
                })
                job_id.sudo().set_recruit()
            else:
                record.job_id.sudo().write({'website_published':True, 'website_description':record.jobdesk})
                record.job_id.sudo().set_recruit()


    ###############################################
    # Button
    ###############################################
    
    # RFA
    def action_rfa(self):
        for record in self:

            record.state = 'rfa'
            approval_line_ids = []
            approval_line_ids.append([0,0,{ 
                'state': record.state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # get approval layer
            layers = self.env['big.fpk.matrix.approval.line'].search([('matrix_id','=',record.matrix_approval_id.id)], order="sequence asc, id asc")
            if layers:
                record.responsible_id = layers[0].id

                # create schedule activity 
                responsible_employee_id = record.validate_user_recipent(responsible_group=record.responsible_id.group_id)
                if responsible_employee_id:
                    for emp in responsible_employee_id:
                        self.env['mail.activity'].create({
                            'note': f'FPK number {record.name} need your approval',
                            'summary': f'Dear Approver of FPK number {record.name}, we need your approval',
                            'date_deadline': datetime.now(),
                            'user_id': emp.user_id.id,
                            'res_id': record.id,
                            'res_model_id': self.env.ref('custom_hr_recruitment.model_big_fpk').id,
                            'activity_type_id': 4 #to do
                        })
    
    # REVISE
    def action_revise(self):
        for record in self:
            # Validate Approval
            record.validate_approval()

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
                'layer_id': record.responsible_id.id,
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")
    
    # reject
    def action_reject(self):
        for record in self:
            # Validate Approval
            record.validate_approval()

            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_reject",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Reject Wizard',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }

            record.state = 'reject'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                'layer_id':record.responsible_id.id,
                'reason': message,
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
            # Validate Approval
            record.validate_approval()

            record.state = 'cancel'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': record.state,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                # activity.action_feedback(feedback="")
                activity.unlink()

    # Set to Draft
    def action_draft(self):
        for record in self:
            record.state = 'draft'

            # give feedback for activity
            for activity in record.activity_ids:
                # activity.action_feedback(feedback="")
                activity.unlink()


    # action approve
    def action_approve(self):
        for record in self:
            # VALIDASI APPROVAL
            record.validate_approval()

            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_approve",
                    # 'default_function_parameter':record.,
                }
                return {
                    'type':'ir.actions.act_window',
                    'name':'Approval Reason',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                }
            
            # check if must fill reason
            if record.responsible_id.need_reason and not message:
                raise ValidationError("Anda harus mengisi reason terlebih dahulu!")

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            # masukan approval ke tabel approval dan ganti step / layer approval
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'state': 'approved',
                'layer_id': record.responsible_id.id,
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})
            
            # ambil list layer yang ada di tabel approval
            layer_list = []
            if record.approval_ids:
                for app in record.approval_ids:
                    if app.state in ['revise','reject']:
                        layer_list = []
                    elif app.layer_id:
                        layer_list.append(app.layer_id.id)
            
            
            domain = [
                ('matrix_id','=',record.matrix_approval_id.id),
                ('id','!=',record.responsible_id.id),
                ('id','not in',layer_list)
            ]
            next_layer = self.env['big.fpk.matrix.approval.line'].search(domain, order="sequence asc, id asc", limit=1)
            if next_layer:
                record.responsible_id = next_layer[0].id

                # create schedule activity 
                responsible_employee_id = record.validate_user_recipent(responsible_group=record.responsible_id.group_id)
                if responsible_employee_id:
                    for emp in responsible_employee_id:
                        self.env['mail.activity'].create({
                            'note': f'FPK number {record.name} need your approval',
                            'summary': f'Dear Approver of FPK number {record.name}, we need your approval',
                            'date_deadline': datetime.now(),
                            'user_id': emp.user_id.id,
                            'res_id': record.id,
                            'res_model_id': self.env.ref('custom_hr_recruitment.model_big_fpk').id,
                            'activity_type_id': 4 #to do
                        })
            else:
                # give feedback for activity
                for activity in record.activity_ids:
                    activity.action_feedback(feedback="")

                # record.sudo().write({'state':'approved', 'approval_ids':approval_line_ids})
                record.sudo().write({'state':'done', 'approval_ids':approval_line_ids})
                
                record.finalize_fpk()

class big_fpk_penggantian_list(models.Model):
    _name = 'big.fpk.penggantian.list'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Permintaan Karyawan (List Penggantian)'
    
    fpk_id = fields.Many2one('big.fpk', string='Form Permintaan Karyawan', ondelete="cascade")

    status = fields.Selection([
        ('keluar', 'Resign / Habis Kontrak'),
        ('promosi', 'Promosi'),
        ('mutasi', 'Mutasi'),
        ('demosi', 'Demosi'),
    ], string='Status', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    date = fields.Date(string='Tanggal', required=True, Tracking=True)


class big_fpk_pendidikan(models.Model):
    _name = 'big.fpk.pendidikan'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Permintaan Karyawan (List Penggantian)'
    
    fpk_id = fields.Many2one('big.fpk', string='Form Permintaan Karyawan', ondelete="cascade")

    pendidikan = fields.Selection([
        ('SD', 'SD'),
        ('SMP', 'SMP'),
        ('SMA', 'SMA'),
        ('S1', 'S1'),
        ('S2', 'S2'),
        ('S3', 'S3'),
    ], string='Status', required=True, tracking=True)
    jurusan = fields.Char('Fakultas / Jurusan', tracking=True)




# approval
class big_fpk_approval_line(models.Model):
    _name = "big.fpk.approval.line"
    _description = 'Form Permintaan Karyawan (Approval Line)'

    fpk_id = fields.Many2one('big.fpk', string='FPK', ondelete="cascade")


    layer_id = fields.Many2one('big.fpk.matrix.approval.line', string='Layer / Stage Approval')
    state = fields.Selection(STATE + [('revise','Revise')], string='State')    
    
    reason = fields.Text('Reason')

    pelaksana_id = fields.Many2one('res.users','Pelaksana', size=128)
    department_id = fields.Many2one(related='pelaksana_id.employee_id.department_id', string="Department")
    job_id = fields.Many2one(related='pelaksana_id.employee_id.job_id', string="Position")

    tanggal = fields.Datetime('Tanggal')





# MATRIX APPROVAL
class big_fpk_matrix_approval(models.Model):
    _name = 'big.fpk.matrix.approval'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Permintaan Karyawan (Approval Matrix)'
    
    name = fields.Char('Name', required=True, tracking=True)
    jenis_fpk = fields.Selection(JENIS_FPK, string='Jenis FPK', required=True, tracking=True)
    department_ids = fields.Many2many('hr.department', string='Specific Department', required=True, tracking=True)
    job_ids = fields.Many2many('hr.job', string='Specific Job Position', tracking=True)

    approval_ids = fields.One2many('big.fpk.matrix.approval.line', 'matrix_id', string='Approval List')

    active = fields.Boolean(string='Active', default=True)

    @api.onchange('jenis_fpk')
    def _onchange_jenis_fpk(self):
        for record in self:
            if record.jenis_fpk in ['penambahan_karyawan','penambahan_jabatan_baru'] and len(record.approval_ids) == 4 and not record.approval_ids.filtered(lambda x: x.group_id == self.env.ref('custom_hr_recruitment.fpk_direksi').id):
                record.approval_ids = [(0,0,{'name': 'Direksi', 'group_id': self.env.ref('custom_hr_recruitment.fpk_direksi').id })]

    
    @api.constrains('job_ids','department_ids','jenis_fpk')
    def _constrains_job_ids(self):
        for record in self:
            if record.job_ids:
                matrix_id = self.env[self._name].search([
                    ('id','!=',record.id),
                    ('jenis_fpk','=',record.jenis_fpk),
                    ('department_ids.id','in',record.department_ids.ids),
                    ('job_ids.id','in',record.job_ids.ids),
                    ('active','=',True)
                ])
                if matrix_id:
                    raise ValidationError(f"Job Tersebut sudah ada di master approval yang lain!\n\n{matrix_id[0].name}")

    @api.model
    def default_get(self, fields_list):
        res = super(big_fpk_matrix_approval, self).default_get(fields_list)
        approval_ids = [
            (0, 0, {'name': 'Approval Head', 'group_id': self.env.ref('custom_hr_recruitment.fpk_head').id }),
            (0, 0, {'name': 'Approval Manager', 'group_id': self.env.ref('custom_hr_recruitment.fpk_manager').id }),
            (0, 0, {'name': 'Approval HR1', 'group_id': self.env.ref('custom_hr_recruitment.fpk_hr1').id }),
            (0, 0, {'name': 'Approval HR2', 'group_id': self.env.ref('custom_hr_recruitment.fpk_hr2').id }),
        ]

        res.update({
            'approval_ids': approval_ids,
        })
        return res

    def unlink(self):
        for record in self:
            raise UserError(_('You cannot Delete this record, Please use Archieve instead of Delete!'))
            return super(big_fpk_matrix_approval, self).unlink()

class big_fpk_matrix_approval_line(models.Model):
    _name = 'big.fpk.matrix.approval.line'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Form Permintaan Karyawan (Approval Matrix Line)'

    matrix_id = fields.Many2one('big.fpk.matrix.approval', string='Matrix Approval', ondelete="cascade")

    def _get_group_id_domain(self):
        domain = [(1,'=',1)]
        
        module_categ = self.env.ref('custom_hr_recruitment.module_cateogry_fpk')
        if module_categ:
            domain = [('category_id','=',module_categ.id)]
        return domain

    sequence = fields.Integer('Sequence', default=1)
    name = fields.Char('Approval Name', required=True)
    group_id = fields.Many2one('res.groups', string='Group', domain=_get_group_id_domain, required=True)
    # employee_id = fields.Many2one('hr.employee', string='Specific Employee (if Exist)')
    employee_ids = fields.Many2many('hr.employee', string='Specific Employee (if Exist)')
    employee_ids_domain = fields.Char(compute="_compute_employee_ids_domain", string="employee_ids_domain")
    @api.depends('group_id')
    def _compute_employee_ids_domain(self):
        for record in self:
            domain = [('user_id','!=',False)]
            if record.group_id:
                domain = [
                    ('user_id','in',record.group_id.users.ids),
                ]
            record.employee_ids_domain = json.dumps(domain)

    need_reason = fields.Boolean('Need fill reason when approve?')