# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


STEP_APPROVAL = [
    ('pengajuan', 'Pengajuan'),
    ('closing', 'Closing'),
    ('done','Done'),
    ('cancel','Canceled'),
]

PENGAJUAN_STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approve1','Approved Manager'),
    ('approve2','HRD Approved'),
    ('approve3','Approved Direksi'),
    ('refuse','Refused'),
    ('cancel','Canceled'),
    ('reject','Rejected'),
]

CLOSING_STATE = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approve0','PIC Sales & Marketing Validated'),
    ('approve1','Approved Manager'),
    ('approve2','Approved HR'),
    ('approve3','PIC F&A validated'),
    ('refuse','Refused'),
    ('cancel','Canceled'),
    ('reject','Rejected'),
]

class dym_perjalanan_dinas(models.Model):
    _name = "dym.perjalanan.dinas"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = "Perjalanan Dinas Karyawan"

    def _get_default_employee(self):
        emp_id = self.env.user.employee_id
        return emp_id

    name = fields.Char(string='Name')

    employee_id = fields.Many2one('hr.employee', string='PIC Perjalanan Dinas', required=True, readonly=True,  
        default=_get_default_employee, tracking=True)
    barcode = fields.Char(related="employee_id.barcode",string='NIK', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", store=True)
    is_sales_marketing = fields.Boolean(related='employee_id.department_id.is_sales_marketing')
    
    job_id = fields.Many2one(related='employee_id.job_id', string='Job Position', store=True)
    job_grade_id = fields.Many2one(related='employee_id.job_grade_id', store=True)


    # UNTUK APPROVAL
    def _get_default_manager(self):
        emp_id = self.env.user.employee_id.parent_id
        return emp_id
    
    def _get_default_sales(self):
        emp_id = False
        group_hr = self.env.ref('dym_perjalanan_dinas.pd_pic_sales')
        if group_hr and group_hr.users:
            emp_id = group_hr.users[0].employee_id.id if group_hr.users[0].employee_id else False
        return emp_id

    def _get_default_hr(self):
        emp_id = False
        group_hr = self.env.ref('dym_perjalanan_dinas.pd_human_resource')
        if group_hr and group_hr.users:
            emp_id = group_hr.users[0].employee_id.id if group_hr.users[0].employee_id else False
        return emp_id
    
    def _get_default_fa(self):
        emp_id = False
        group_hr = self.env.ref('dym_perjalanan_dinas.pd_fat')
        if group_hr and group_hr.users:
            emp_id = group_hr.users[0].employee_id.id if group_hr.users[0].employee_id else False
        return emp_id
    
    def _get_default_director(self):
        emp_id = False
        department = self.env['hr.department'].search([('is_bod','=',True)],limit=1)
        if department and department.manager_id:
            emp_id = department.manager_id.id
        return emp_id
    

    pic_sales_id = fields.Many2one('hr.employee', string='PIC Sales & Marketing', default=_get_default_sales, tracking=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', default=_get_default_manager, tracking=True)
    hr_responsible_id = fields.Many2one('hr.employee', string='HR Responsible', default=_get_default_hr, tracking=True)
    direksi_id = fields.Many2one('hr.employee', string='Direksi', default=_get_default_director, tracking=True)
    pic_fa_id = fields.Many2one('hr.employee', string='PIC Finance & Accounting', default=_get_default_fa, tracking=True)
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            record.manager_id = record.employee_id.parent_id


    is_need_pic_sales_validate = fields.Boolean(compute='_compute_is_need_pic_sales_validate', string='Is Need PIC Sales Validate', store=True)
    @api.depends('employee_id','employee_id.department_id','employee_id.department_id.is_sales_marketing','is_sales_marketing','write_date')
    def _compute_is_need_pic_sales_validate(self):
        for record in self:
            is_need_pic_sales_validate = False
            if record.step_approval == 'closing' and record.closing_state == 'rfa' and record.is_sales_marketing:
                is_need_pic_sales_validate = True

            record.is_need_pic_sales_validate = is_need_pic_sales_validate


    employee_ids = fields.Many2many(
        comodel_name="hr.employee", 
        relation="perjalanan_dinas_employee_rel",
        column1="employee_id", 
        column2="perjalanan_dinas_id", 
        string="Karyawan lainnya",tracking=True)
    
    @api.constrains('employee_ids')
    def _constrains_employee_ids(self):
        for record in self:
            if record.employee_id.id in record.employee_ids.ids:
                raise ValidationError(f"Employee yang diinput pada Field Karyawan lainnya telah penjadi PIC di perjalanan dinas ini ! \n\n {record.employee_id.name}")

    tujuan = fields.Selection([
        ('wonogiri', 'Plant Wonogiri'),
        ('lainnya', 'Lainnya'),
    ], string='Tujuan', required=True, tracking=True)

    kota_tujuan = fields.Char(string='Kota Tujuan', tracking=True)
    @api.onchange('tujuan')
    def _onchange_tujuan(self):
        for record in self:
            if record.tujuan == 'wonogiri':
                record.kota_tujuan = ''

    tgl_berangkat = fields.Date('Tgl Berangkat', required=True, tracking=True)
    tgl_kembali = fields.Date('Tgl Kembali', required=True, tracking=True)

    @api.constrains('tgl_berangkat','tgl_kembali')
    def _constrains_tgl_berangkat_kembali(self):
        for record in self:
            if record.tgl_kembali and record.tgl_berangkat and record.tgl_berangkat > record.tgl_kembali:
                raise ValidationError('Tanggal kembali tidak boleh lebih besar dari tgl berangkat!')

    jangka_waktu = fields.Integer(compute='_compute_jangka_waktu', string='Jangka Waktu')
    @api.depends('tgl_berangkat','tgl_kembali')
    def _compute_jangka_waktu(self):
        for record in self:
            jangka_waktu = 0
            if record.tgl_kembali and record.tgl_berangkat:
                delta = record.tgl_kembali - record.tgl_berangkat
                jangka_waktu = delta.days + 1
            record.jangka_waktu = jangka_waktu


    description_perjalanan = fields.Text(string='Tujuan Perjalanan', required=True, tracking=True)


    # attendance & timeoff monitoring
    attendance_ids = fields.Many2many('hr.attendance', compute='_compute_attendance_timeoff', string='Attendance list')
    timeoff_ids = fields.Many2many('hr.leave', compute='_compute_attendance_timeoff', string='Timeoff list')

    @api.depends('employee_id','employee_ids','tgl_berangkat','tgl_kembali','write_date')
    def _compute_attendance_timeoff(self):
        for record in self:
            attendance_ids = []
            timeoff_ids = []

            employee_list = [record.employee_id.id]
            for emp in record.employee_ids:
                employee_list.append(emp.id)

            # get attendance
            attendances = self.env['hr.attendance'].sudo().search([
                ('employee_id','in',employee_list),
                ('check_in','>=',record.tgl_berangkat),
                ('check_in','<=',record.tgl_kembali)
            ])
            attendance_ids = [x.id for x in attendances] if attendances else attendance_ids

            # get timeoff
            timeoffs = self.env['hr.leave'].sudo().search([
                ('employee_id','in',employee_list),
                ('date_to','>=', record.tgl_berangkat),
                ('date_from','<=', record.tgl_kembali),
            ])
            timeoff_ids = [x.id for x in timeoffs] if timeoffs else timeoff_ids



            record.attendance_ids = attendance_ids
            record.timeoff_ids = timeoff_ids


    
    # rincian perjalanan dinas
    rincian_transportasi_ids = fields.One2many('perjalanan.dinas.rincian.transportasi', 'pd_id', string='Rincian Transportasi', tracking=True)
    rincian_akomodasi_ids = fields.One2many('perjalanan.dinas.rincian.akomodasi', 'pd_id', string='Rincian Akomodasi', tracking=True)
    rincian_lain_ids = fields.One2many('perjalanan.dinas.rincian.lain', 'pd_id', string='Rincian Lain-lain', tracking=True)

    grand_total_lebih = fields.Float(compute="_compute_grand_total_lebihkurang", string='Grand Total lebih', store=True)
    grand_total_kurang = fields.Float(compute="_compute_grand_total_lebihkurang", string='Grand Total kurang', store=True)
    
    @api.depends('rincian_transportasi_ids','rincian_akomodasi_ids','rincian_lain_ids')
    def _compute_grand_total_lebihkurang(self):
        for record in self:
            rincian_transportasi_lebih = 0
            rincian_transportasi_kurang = 0
            if record.rincian_transportasi_ids:
                rincian_transportasi_lebih = sum([x.lebih for x in record.rincian_transportasi_ids.filtered(lambda x: x.lebih > 0)])
                rincian_transportasi_kurang = sum([x.kurang for x in record.rincian_transportasi_ids.filtered(lambda x: x.kurang > 0)])

            rincian_akomodasi_lebih = 0
            rincian_akomodasi_kurang = 0
            if record.rincian_akomodasi_ids:
                rincian_akomodasi_lebih = sum([x.lebih for x in record.rincian_akomodasi_ids.filtered(lambda x: x.lebih > 0)])
                rincian_akomodasi_kurang = sum([x.kurang for x in record.rincian_akomodasi_ids.filtered(lambda x: x.kurang > 0)])
            
            rincian_lain_lebih = 0
            rincian_lain_kurang = 0
            if record.rincian_lain_ids:
                rincian_lain_lebih = sum([x.lebih for x in record.rincian_lain_ids.filtered(lambda x: x.lebih > 0)])
                rincian_lain_kurang = sum([x.kurang for x in record.rincian_lain_ids.filtered(lambda x: x.kurang > 0)])
            
            record.grand_total_lebih = rincian_transportasi_lebih + rincian_akomodasi_lebih + rincian_lain_lebih
            record.grand_total_kurang = rincian_transportasi_kurang + rincian_akomodasi_kurang + rincian_lain_kurang

    @api.constrains('rincian_akomodasi_ids')
    def _constrains_rincian_akomodasi_ids(self):
        for record in self:
            if record.tujuan != 'wonogiri' and len(record.rincian_akomodasi_ids) >=1 and record.rincian_akomodasi_ids.filtered(lambda x: x.rincian == 'mess'):
                raise ValidationError('Anda tidak dapat memilih rincian "MESS" jika tujuan dinas bukan ke WONOGIRI!')

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(dym_perjalanan_dinas, self).default_get(fields_list)
    #     rincian_transportasi_ids = [
    #         (0, 0, {'rincian': '1. MOBIL PERUSAHAAN/ RENTAL', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '-- a. BAHAN BAKAR', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '-- b. TOL', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '-- c. PARKIR', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '2. KERETA API', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '3. PESAWAT', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '4. TAXI', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '5. LAIN-LAIN', 'budget': 0, 'realisasi':0}),
    #     ]

    #     rincian_akomodasi_ids = [
    #         (0, 0, {'rincian': '1. HOTEL/MESS', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '2. LAUNDRY', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '3. LAIN-LAIN', 'budget': 0, 'realisasi':0}),
    #     ]
        
    #     rincian_lain_ids = [
    #         (0, 0, {'rincian': '1. MAKAN', 'budget': 0, 'realisasi':0}),
    #         (0, 0, {'rincian': '2. LAIN-LAIN', 'budget': 0, 'realisasi':0}),
    #     ]


    #     res.update({
    #         'rincian_transportasi_ids': rincian_transportasi_ids,
    #         'rincian_akomodasi_ids': rincian_akomodasi_ids,
    #         'rincian_lain_ids': rincian_lain_ids,
    #     })
    #     return res

    note = fields.Text('Note')


    approval_ids = fields.One2many('perjalanan.dinas.approval.line','pd_id', string='Perjalanan Dinas Approval Line')
    
    
    
    step_approval = fields.Selection(STEP_APPROVAL, 
        string='Step Approval',
        default='pengajuan',
        readonly=True,
        required=True, tracking=True)
    step_approval_done = fields.Selection(related='step_approval', string='State')
    step_approval_cancel = fields.Selection(related='step_approval', string='State')
    

    pengajuan_state = fields.Selection(PENGAJUAN_STATE,
        string='Pengajuan State',
        default='draft',
        readonly=True,
        required=True, tracking=True)    

    pengajuan_state_refuse = fields.Selection(related='pengajuan_state', string='State')
    pengajuan_state_cancel = fields.Selection(related='pengajuan_state', string='State')
    pengajuan_state_reject = fields.Selection(related='pengajuan_state', string='State')
    
    closing_state = fields.Selection(CLOSING_STATE,
        string='Closing State',
        default='draft',
        readonly=True,
        required=True, tracking=True)    

    closing_state_refuse = fields.Selection(related='closing_state', string='State')
    closing_state_cancel = fields.Selection(related='closing_state', string='State')
    closing_state_reject = fields.Selection(related='closing_state', string='State')



    # untuk printout
    # pengajuan
    # pemohon_id = fields.Many2one('hr.employee', compute='_compute_pemohon', string='Pemohon')
    # pemohon_date = fields.Datetime(compute='_compute_pemohon', string='Pemohon Date')
    
    # @api.depends('approval_ids','approval_ids.pelaksana_id','approval_ids.tanggal')
    # def _compute_pemohon(self):
    #     for record in self:
    #         record.pemohon_id = None
    #         record.pemohon_date = None
    #         if record.approval_ids:
    #             record.pemohon_id = record.approval_ids.filtered(lambda x: x.step_approval == 'pengajuan' and x.pengajuan_state == 'rfa')[-1].pelaksana_id.employee_id
    #             record.pemohon_date = record.approval_ids.filtered(lambda x: x.step_approval == 'pengajuan' and x.pengajuan_state == 'rfa')[-1].tanggal


    # closing
    pelapor_id = fields.Many2one('hr.employee', compute='_compute_pelapor_menyetujui_mengetahui', string='Pelapor')
    pelapor_date = fields.Datetime(compute='_compute_pelapor_menyetujui_mengetahui', string='Pelapor Date')

    menyetujui_id = fields.Many2one('hr.employee', compute='_compute_pelapor_menyetujui_mengetahui', string='Menyetujui')
    menyetujui_date = fields.Datetime(compute='_compute_pelapor_menyetujui_mengetahui', string='Menyetujui Date')

    mengetahui_id = fields.Many2one('hr.employee', compute='_compute_pelapor_menyetujui_mengetahui', string='Mengetahui')
    mengetahui_date = fields.Datetime(compute='_compute_pelapor_menyetujui_mengetahui', string='Mengetahui Date')
    
    @api.depends('approval_ids','approval_ids.pelaksana_id','approval_ids.tanggal')
    def _compute_pelapor_menyetujui_mengetahui(self):
        for record in self:
            record.pelapor_id = None
            record.pelapor_date = None
            record.menyetujui_id = None
            record.menyetujui_date = None
            record.mengetahui_id = None
            record.mengetahui_date = None
            if record.approval_ids:
                record.pelapor_id = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'rfa')[-1].pelaksana_id.employee_id
                record.pelapor_date = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'rfa')[-1].tanggal

                record.menyetujui_id = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'approve1')[-1].pelaksana_id.employee_id
                record.menyetujui_date = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'approve1')[-1].tanggal

                record.mengetahui_id = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'approve2')[-1].pelaksana_id.employee_id
                record.mengetahui_date = record.approval_ids.filtered(lambda x: x.step_approval == 'closing' and x.closing_state == 'approve2')[-1].tanggal

    
    @api.model
    def create(self, values):
        # values['name'] = 'HD.UDS'
        res = super(dym_perjalanan_dinas,self).create(values)
        name =  self.env['ir.sequence'].get_sequence(self._name, 'SPD')
        dep_name = f'/{res.department_id.name}' if res.department_id else '/'
        res.name = name + dep_name
        return res

    def unlink(self):
        for record in self:
            if record.pengajuan_state != 'draft':
                raise ValidationError(_('Tidak bisa menghapus data dengan state selain DRAFT!'))
            res = super(dym_perjalanan_dinas,self).unlink()
            return res
    
    ###############################################
    # Pengajuan
    ###############################################

    # RFA
    def action_pengajuan_rfa(self):
        for record in self:
            record.pengajuan_state = 'rfa'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': None,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # create schedule activity 
            if record.manager_id and record.manager_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Pengajuan Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': record.manager_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })

    # APPROVE MANAGER
    def action_pengajuan_approve1(self):
        for record in self:
            record.pengajuan_state = 'approve1'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': None,
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
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear HR Responsible for {record.name}, we need your approval for Pengajuan Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': record.hr_responsible_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })

    # APPROVE HRD
    def action_pengajuan_approve2(self):
        for record in self:
            record.pengajuan_state = 'approve2'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': None,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            # create schedule activity 
            if record.direksi_id and record.direksi_id.user_id and record.direksi_id.id != record.manager_id.id:
                self.env['mail.activity'].create({
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear Direksi user, we need your approval for Pengajuan Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': record.direksi_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })
            else:
                # kalau direksi sama managernya sama maka set state pengajuan = done
                record.step_approval = 'closing'
    
    # APPROVE DIREKSI
    def action_pengajuan_approve3(self):
        for record in self:
            record.pengajuan_state = 'approve3'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': None,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            record.step_approval = 'closing'

            # create schedule activity 
            # if record.direksi_id and record.direksi_id.user_id:
            #     self.env['mail.activity'].create({
            #         'note': f'Perjalanan dinas number {record.name} need your approval',
            #         'summary': 'Pengajuan Perjalanan Dinas need an Approval',
            #         'date_deadline': datetime.now(),
            #         'user_id': record.direksi_id.user_id.id,
            #         'res_id': record.id,
            #         'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
            #         'activity_type_id': 4 #to do
            #     })


    # REJECT
    def action_pengajuan_reject(self):
        for record in self:
            record.pengajuan_state = 'reject'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

    # REVISE
    def action_pengajuan_revise(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_pengajuan_revise",
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

            record.pengajuan_state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': 'revise',
                # 'closing_state': record.closing_state,
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

    # Set to Draft
    def action_pengajuan_set_draft(self):
        for record in self:
            record.pengajuan_state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'pengajuan_state': record.pengajuan_state,
                # 'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

    ################################################
    # Pengajuan
    ###############################################

    ###############################################
    # Closing
    ###############################################

    # RFA
    def action_closing_rfa(self):
        for record in self:
            record.closing_state = 'rfa'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                # 'pengajuan_state': record.pengajuan_state,
                'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # create schedule activity 
            if record.is_sales_marketing:
                # for PIC Sales and marketing
                user_id = record.pic_sales_id.user_id.id if record.pic_sales_id.user_id else False
                if user_id and self.env['res.users'].sudo().browse(user_id):
                    self.env['mail.activity'].create({
                        'note': f'Perjalanan dinas number {record.name} need your approval',
                        'summary': f'Dear PIC Sales and Marketing for {record.name}, we need your approval for Closing Perjalanan Dinas',
                        'date_deadline': datetime.now(),
                        'user_id': user_id,
                        'res_id': record.id,
                        'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                        'activity_type_id': 4 #to do
                    })
                pass
            else:
                # for manager
                if record.manager_id and record.manager_id.user_id:
                    self.env['mail.activity'].create({
                        'note': f'Perjalanan dinas number {record.name} need your approval',
                        'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Closing Perjalanan Dinas',
                        'date_deadline': datetime.now(),
                        'user_id': record.manager_id.user_id.id,
                        'res_id': record.id,
                        'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                        'activity_type_id': 4 #to do
                    })

    # Validate PIC Sales Marketing
    def action_closing_approve0(self):
        for record in self:
            record.closing_state = 'approve0'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                # 'pengajuan_state': record.pengajuan_state,
                'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            # create schedule activity 
            if record.manager_id and record.manager_id.user_id:
                self.env['mail.activity'].create({
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear manager of {record.employee_id.name}, we need your approval for Closing Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': record.manager_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })
    

    # APPROVE MANAGER
    def action_closing_approve1(self):
        for record in self:
            record.closing_state = 'approve1'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                # 'pengajuan_state': record.pengajuan_state,
                'closing_state': record.closing_state,
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
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear HR Responsible for {record.name}, we need your approval for Closing Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': record.hr_responsible_id.user_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })
    
    # APPROVE HR
    def action_closing_approve2(self):
        for record in self:
            record.closing_state = 'approve2'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'closing_state': record.closing_state,
                # 'closing_state': None,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

            # create schedule activity 
            # for pic f&a
            user_id = record.pic_fa_id.user_id.id if record.pic_fa_id.user_id else False
            if user_id and self.env['res.users'].sudo().browse(user_id):
                self.env['mail.activity'].create({
                    'note': f'Perjalanan dinas number {record.name} need your approval',
                    'summary': f'Dear PIC Finance & Accounting for {record.name}, we need your validation for Closing Perjalanan Dinas',
                    'date_deadline': datetime.now(),
                    'user_id': user_id,
                    'res_id': record.id,
                    'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
                    'activity_type_id': 4 #to do
                })

    # APPROVE F&A Validation
    def action_closing_approve3(self):
        for record in self:
            record.closing_state = 'approve3'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                'closing_state': record.closing_state,
                # 'closing_state': None,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids:
                activity.action_feedback(feedback="")

            record.step_approval = 'done'

            # create schedule activity 
            # if record.direksi_id and record.direksi_id.user_id:
            #     self.env['mail.activity'].create({
            #         'note': f'Perjalanan dinas number {record.name} need your approval',
            #         'summary': 'Pengajuan Perjalanan Dinas need an Approval',
            #         'date_deadline': datetime.now(),
            #         'user_id': record.direksi_id.user_id.id,
            #         'res_id': record.id,
            #         'res_model_id': self.env.ref('dym_perjalanan_dinas.model_dym_perjalanan_dinas').id,
            #         'activity_type_id': 4 #to do
            #     })


    # REVISE
    def action_closing_revise(self):
        for record in self:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':record.id,
                    'default_model_name':record._name,
                    'default_function_name':"action_closing_revise",
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

            record.closing_state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                # 'pengajuan_state': 'revise',
                'closing_state': 'revise',
                'reason': message,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")

    # Set to Draft
    def action_closing_set_draft(self):
        for record in self:
            record.closing_state = 'draft'
            approval_line_ids = []
            approval_line_ids.append([0,0,{
                'step_approval': record.step_approval,
                # 'pengajuan_state': record.pengajuan_state,
                'closing_state': record.closing_state,
                # 'reason': ,
                'pelaksana_id': self.env.user.id,
                'tanggal':datetime.today(),
            }])
            record.sudo().write({'approval_ids':approval_line_ids})

            # give feedback for activity
            for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
                activity.action_feedback(feedback="")


    ###############################################
    # Closing
    ###############################################

    

    # def action_cancel(self):
    #     for record in self:
    #         approval_line_ids = []
    #         approval_line_ids.append([0,0,{
    #             'step_approval': record.step_approval,
    #             'pengajuan_state': record.pengajuan_state,
    #             'closing_state': record.closing_state,
    #             # 'reason': ,
    #             'pelaksana_id': self.env.user.id,
    #             'tanggal':datetime.today(),
    #         }])
    #         record.sudo().write({'approval_ids':approval_line_ids})

    #         # give feedback for activity
    #         for activity in record.activity_ids.filtered(lambda x: x.user_id.id == self.env.user.id):
    #             activity.action_feedback(feedback="")

    #         record.step_approval = 'done'
    

class perjalanan_dinas_rincian_transportasi(models.Model):
    _name = "perjalanan.dinas.rincian.transportasi"
    _description = 'Perjalanan Dinas (Rincian Transportasi)'

    pd_id = fields.Many2one('dym.perjalanan.dinas','Perjalanan Dinas', ondelete="cascade")
    step_approval = fields.Selection(related='pd_id.step_approval')
    pengajuan_state = fields.Selection(related='pd_id.pengajuan_state')
    closing_state = fields.Selection(related='pd_id.closing_state')

    # rincian = fields.Char(string='Rincian / Uraian')
    rincian = fields.Selection([
        ('mobil', 'MOBIL PERUSAHAAN/ RENTAL'),
        ('bahan_bakar', 'BAHAN BAKAR'),
        ('tol', 'TOL'),
        ('parkir', 'PARKIR'),
        ('kereta', 'KERETA API'),
        ('pesawat', 'PESAWAT'),
        ('taxi', 'TAXI'),
        ('lainnya', 'LAIN-LAIN'),
    ], string='Rincian',required=True)
    
    budget = fields.Float(string='Budget', default=0, digits=(16,0))
    realisasi = fields.Float(string='Realisasi', default=0, digits=(16,0))
    ref = fields.Char('Ref')

    lebih = fields.Float(compute="_compute_lebih_kurang", string='Lebih', store=True, digits=(16,0))
    kurang = fields.Float(compute="_compute_lebih_kurang", string='Kurang', store=True, digits=(16,0))
    
    @api.depends('budget','realisasi')
    def _compute_lebih_kurang(self):
        for record in self:
            record.lebih = record.budget - record.realisasi if record.budget > record.realisasi else 0
            record.kurang = record.realisasi - record.budget if record.realisasi > record.budget else 0

    dinas_file = fields.Many2many('ir.attachment', string='Attachments') 
    dinas_file_rel = fields.Many2many(related="dinas_file") 

    # attachment = fields.Binary(string='Lampiran', attachment=True, store=True, tracking=True)
    # attachment_filename = fields.Char(string='Filename Lampiran', tracking=True)
    # attachment_web_url = fields.Char(compute='_compute_attachment_web_url', string='URL Lampiran', store=True)
    # @api.depends('attachment','attachment_filename')
    # def _compute_attachment_web_url(self):
    #     for record in self:
    #         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #         attachment_web_url = ""
    #         domain = [
    #             ('res_model', '=', record._name),
    #             ('res_field', '=', 'attachment'),
    #             ('res_id', '=', record.id),
    #         ]
    #         attachment = self.env['ir.attachment'].search(domain)
    #         if attachment and base_url:
    #             attachment_web_url = f"{base_url}{attachment.website_url}"
    #         record.attachment_web_url = attachment_web_url

    @api.constrains('rincian')
    def _constrains_rincian(self):
        for record in self:
            if not record.rincian:
                raise ValidationError("Anda Harus input rincian terlebih dahulu!")
            
    def unlink(self):
        for record in self:
            if record.pd_id.pengajuan_state != 'draft':
                raise ValidationError('Anda tidak boleh menghapus line pada rincian ini saat sedang closing!\n\n')
            res = super(perjalanan_dinas_rincian_transportasi,self).unlink()
            return res

class perjalanan_dinas_rincian_akomodasi(models.Model):
    _name = "perjalanan.dinas.rincian.akomodasi"
    _inherit = "perjalanan.dinas.rincian.transportasi"
    _description = 'Perjalanan Dinas (Rincian Akomodasi)'
    
    rincian = fields.Selection([
        ('hotel', 'HOTEL'),
        ('mess', 'MESS'),
        ('laundry', 'LAUNDRY'),
        ('lainnya', 'LAIN-LAIN'),
    ], string='Rincian', required=True)

class perjalanan_dinas_rincian_lain(models.Model):
    _name = "perjalanan.dinas.rincian.lain"
    _inherit = "perjalanan.dinas.rincian.transportasi"
    _description = 'Perjalanan Dinas (Rincian lain2)'

    rincian = fields.Selection([
        ('makan', 'MAKAN'),
        ('lainnya', 'LAIN-LAIN'),
    ], string='Rincian', required=True)

class dym_pd_approval_line(models.Model):
    _name = "perjalanan.dinas.approval.line"
    _description = 'Perjalanan Dinas (approval line)'

    pd_id = fields.Many2one('dym.perjalanan.dinas','Perjalanan Dinas Approval Form')

    step_approval = fields.Selection(STEP_APPROVAL, 
        string='Step Approval')
    
    pengajuan_state = fields.Selection(PENGAJUAN_STATE + [('revise','Revised')], string='Pengajuan State')
    closing_state = fields.Selection(CLOSING_STATE + [('revise','Revised')], string='Closing State')

    state = fields.Char(compute='_compute_state', string='State')
    @api.depends('pengajuan_state','closing_state')
    def _compute_state(self):
        for record in self:
            record.state = ''
            if record.pengajuan_state:
                record.state = dict(record._fields['pengajuan_state'].selection).get(record.pengajuan_state) 
            elif record.closing_state:
                record.state = dict(record._fields['closing_state'].selection).get(record.closing_state) 
    
    reason = fields.Text('Reason')

    pelaksana_id = fields.Many2one('res.users','Pelaksana', size=128)
    department_id = fields.Many2one(related='pelaksana_id.employee_id.department_id', string="Department")
    job_id = fields.Many2one(related='pelaksana_id.employee_id.job_id', string="Position")

    tanggal = fields.Datetime('Tanggal')