from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

_STATES = [
    ('draft','Draft'),
    ('rfa','Waiting for Approval'),
    ('approved', 'Approved'),
    ('processing','HR Processing'),
    ('done', 'Done'),
    ('cancel','Canceled'),
    ('refuse','Refuse'),
    ('revise','Revise'),
    ('not_recommended','Not Recommended'),
    ('recommended','Recommended'),
]

class hr_promosi_demosi_mutasi(models.Model):
    _name = 'hr.promosi.demosi.mutasi'
    _description = "FPSK (Promosi / Demosi / Mutasi)"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string="Name", default=lambda self: ('New'), copy=False, index=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    employee_id = fields.Many2one('hr.employee', copy=False, string="Employee", required=True)
    barcode = fields.Char(string="NIK", related='employee_id.barcode')
    identification_id = fields.Char(string="No. KTP", related='employee_id.identification_id')
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.new_dept_id = rec.old_dept_id.id
                rec.new_section_id = rec.old_section_id.id
                rec.new_job_id = rec.old_job_id.id
                rec.new_jam_kerja = rec.old_jam_kerja.id
                rec.new_employee_state = rec.old_employee_state.id

    pdm_type = fields.Selection(
        string='Jenis Perubahan',
        selection=[
            ('pm', 'PROMOSI'), 
            ('dm', 'DEMOSI'),
            ('ac', 'ACTING'),
            ('rt', 'ROTASI'),
            ('mt', 'MUTASI'),
            ('ek', 'EVALUASI KARYAWAN'),
        ], tracking=True, required=True)
    @api.onchange('pdm_type')
    def _onchange_pdm_type(self):
        for rec in self:
            if rec.pdm_type != 'ac':
                rec.acting_start_date = False
                rec.acting_end_date = False

    pdm_reason = fields.Text(string='Alasan')
    pdm_attachment = fields.Binary(string='Attachment', attachment=True)
    tgl_masuk = fields.Date(string="Tanggal Masuk", track_visibility='onchange', related='employee_id.join_date')

    state = fields.Selection(selection=_STATES, string="Status", index=True,  tracking=True, 
        copy=False, default="draft")
    state_cancel = fields.Selection(related="state", tracking=False)
    state_revise = fields.Selection(related="state", tracking=False)
    state_refuse = fields.Selection(related="state", tracking=False)

    # old
    old_dept_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Department")
    old_section_id = fields.Many2one('hr.department', related='employee_id.section', string="Section")
    old_job_id = fields.Many2one('hr.job', related='employee_id.job_id', string="Jabatan Lama")
    old_jam_kerja = fields.Many2one('resource.calendar', string="Jam Kerja Lama", related="employee_id.resource_calendar_id")
    old_employee_state = fields.Many2one('hr.employee.type',string="Status Karyawan", related='employee_id.employee_type_id')

    # new
    new_dept_id = fields.Many2one('hr.department', string="Department", required=True)
    new_section_id = fields.Many2one('hr.department', string="Section")
    new_job_id = fields.Many2one('hr.job', string="Jabatan Baru", required=True)
    new_jam_kerja = fields.Many2one('resource.calendar', string="Jam Kerja Baru")
    new_tgl_masuk = fields.Date(string="Terhitung Mulai Tanggal", default=fields.Datetime.now, track_visibility='onchange')
    new_employee_state = fields.Many2one('hr.employee.type',string="Status Karyawan")

    # acting
    acting_start_date = fields.Date(string="Periode Acting Start", store=True, tracking=True)
    acting_end_date = fields.Date(string="Periode Acting End", store=True, tracking=True)
    acting_month = fields.Integer(store=True, readonly=True, compute="_compute_acting_interval")
    acting_day = fields.Integer(store=True, readonly=True, compute="_compute_acting_interval")
    @api.depends('acting_start_date', 'acting_end_date')
    def _compute_acting_interval(self):
        if self.acting_start_date and self.acting_end_date:
            d0 = date(self.acting_start_date.year, self.acting_start_date.month, self.acting_start_date.day)
            d1 = date(self.acting_end_date.year, self.acting_end_date.month, self.acting_end_date.day) + timedelta(days=1)
            diff = relativedelta(d1, d0)
            self.acting_month = diff.months
            self.acting_day = diff.days
        else:
            self.acting_month = False
            self.acting_day = False

    # evaluasi karyawan
    periode_perpanjangan_start_date = fields.Date(string="Periode Perpanjangan Start", store=True, tracking=True)
    periode_perpanjangan_end_date = fields.Date(string="Periode Perpanjangan End", store=True, tracking=True)
    periode_perpanjangan_year = fields.Integer(store=True, readonly=True, compute="_compute_perpanjangan_interval")
    periode_perpanjangan_month = fields.Integer(store=True, readonly=True, compute="_compute_perpanjangan_interval")
    periode_perpanjangan_day = fields.Integer(store=True, readonly=True, compute="_compute_perpanjangan_interval")
    @api.depends('periode_perpanjangan_start_date', 'periode_perpanjangan_end_date')
    def _compute_perpanjangan_interval(self):
        if self.periode_perpanjangan_start_date and self.periode_perpanjangan_end_date:
            d0 = date(self.periode_perpanjangan_start_date.year, self.periode_perpanjangan_start_date.month, self.periode_perpanjangan_start_date.day)
            d1 = date(self.periode_perpanjangan_end_date.year, self.periode_perpanjangan_end_date.month, self.periode_perpanjangan_end_date.day) + timedelta(days=1)
            diff = relativedelta(d1, d0)
            self.periode_perpanjangan_year = diff.years
            self.periode_perpanjangan_month = diff.months
            self.periode_perpanjangan_day = diff.days
        else:
            self.periode_perpanjangan_year = False
            self.periode_perpanjangan_month = False
            self.periode_perpanjangan_day = False

    # @api.onchange('new_dept_id')
    # def _onchange_new_dept_id(self):
    #     child = self.env['hr.department'].search([('parent_id', '=', self.new_dept_id.id)]).ids
    #     domain = {'domain': {'new_section_id': [('id', 'in', child)]}}
    #     self.new_section_id = False
    #     return domain
    
    # Kebutuhan Approval
    # @api.model
    # def _default_loa(self):
    #     dt = self.env['matrix.approval'].search([('model_id.name', '=', self._name)], order="id asc", limit=1)
    #     return dt.id if dt else False
    
    matrix_id = fields.Many2one('matrix.approval', string='Matrix Approval', required=True,
        domain=[('model_id.model', '=', 'hr.promosi.demosi.mutasi'),('active','=',True)]) # default=_default_loa
    responsible_id = fields.Many2one('matrix.approval.line', string='Layer / Approval Stage', readonly=True)
    approval_info_ids = fields.Many2many('matrix.approval.info','pdm_approval_line','pdm_id','approval_id', 
        string='Approval Information', store=True)
    next_approve_user_ids = fields.Many2many('res.users', 'pdm_res_user', 'pdm_id', 'user_id', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")

    @api.onchange('new_dept_id','new_job_id')
    def _onchange_for_matrix_id(self):
        for rec in self:
            rec.matrix_id = False
            if rec.new_dept_id and rec.new_job_id:
                matrix_search = self.env['matrix.approval'].search([
                    ('department_ids','in',[rec.new_dept_id.id]),
                    ('job_ids','in',[rec.new_job_id.id]),
                    ('model_id.name','=',self._description),
                    ])
                if matrix_search:
                    rec.matrix_id = matrix_search.id
                else:
                    raise ValidationError("Matrix Approval pada Department dan Job Position Berikut Tidak Tersedia, Silahkan Hubungi HRD!")

    @api.depends()
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state in ['draft','revise'] and self.env.user.id == rec.create_uid.id

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.is_user_approve_now = False
            if rec.next_approve_user_ids and rec.state == 'rfa':
                rec.is_user_approve_now = self.env.user in rec.next_approve_user_ids

    @api.onchange('matrix_id')
    def _onchange_matrix_id(self):
        for rec in self:
            app_inf = []
            rec.approval_info_ids = False
            if rec.matrix_id:
                dtLine = self.env['matrix.approval.line'].search([('matrix_id','=',rec.matrix_id.id)], order='sequence asc')
                for i in dtLine:
                    tmp = [0,0,{
                        'sequence': i.sequence,
                        'matrix_id': i.matrix_id.id,
                        'model_id': self.matrix_id.model_id.id,
                        'trx_id': False,
                        'matrix_line_id': i.id,
                        'user_ids': i.user_ids,
                        'is_approve': False,
                        'approve_user_id': False,
                        'approve_date': False,
                        'approver_sign': False,
                        'group_id': i.group_id.id
                    }]
                    app_inf.append(tmp)
            rec.approval_info_ids = app_inf

    @api.depends()
    def _compute_next_approval(self):
        for rec in self:
            rec.next_approve_user_ids = False
            if rec.approval_info_ids and rec.state in ['rfa','draft']:
                for i in rec.approval_info_ids:
                    if not i.is_approve:
                        group_user = self.env['res.groups'].sudo().search([('id','=',i.group_id.id)])
                        rec.next_approve_user_ids = i.user_ids if i.user_ids else group_user.users.ids
                        rec.responsible_id = i.matrix_line_id
                        break

    def send_schedule_actifity(self):
        for usr in self.next_approve_user_ids:
            todos = {
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)]).id,
                'user_id': usr.id,
                'summary': 'Request Approval',
                'note': '',
                'activity_type_id': 4,
                'date_deadline': datetime.now(),
            }
            self.env['mail.activity'].sudo().create(todos)

    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(
                    _(
                        "You can't request an approval for a FPSK "
                        "which is empty. (%s)"
                    )
                    % rec.name
                )

    def button_to_approve(self):
        if self.state == 'revise':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    i.sudo().unlink()

            dtLine = self.env['matrix.approval.line'].search([('matrix_id','=',self.matrix_id.id)], order='sequence asc')
            app_inf = []
            for i in self.approval_info_ids:
                tmp = [4, i.id, False]
                app_inf.append(tmp)

            for i in dtLine:
                tmp = [0, 0, {
                        'sequence': i.sequence,
                        'matrix_id': i.matrix_id.id,
                        'model_id': i.matrix_id.model_id.id,
                        'trx_id': False,
                        'matrix_line_id': i.id,
                        'user_ids': i.user_ids,
                        'is_approve': False,
                        'approve_user_id': False,
                        'approve_date': False,
                        'approver_sign': False,
                        'group_id': i.group_id.id
                    }]
                app_inf.append(tmp)
            self.approval_info_ids = app_inf

        self.sudo().to_approve_allowed_check()
        if self.matrix_id:
            self.sudo().write({'state': 'rfa'})
            self.sudo().send_schedule_actifity()
        return 
    
    def button_rejected(self):
        return self.sudo().write({"state": "rejected"})
    
    def button_approved(self):
        message = ""
        if self.responsible_id.need_reason:
            okey = self._context.get('okey',False)
            message = self._context.get('message',False)

            if not okey:
                context = {
                    'default_message': "",
                    'default_data_id':self.id,
                    'default_model_name':self._name,
                    'default_function_name':"button_approved",
                    # 'default_function_parameter':record.,
                }
                return{
                    'type':'ir.actions.act_window',
                    'name':'Approve Reason',
                    'res_model':'revise.wizard',
                    'view_type':'form',
                    'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                    # 'view_type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'context':context                
                    }
        
        maxSeq = max(self.approval_info_ids.mapped('sequence'))
        lastApprove = False
        if self.approval_info_ids and self.state == 'rfa':
            for i in self.approval_info_ids:
                if not i.is_approve:
                    i.sudo().write({
                        'state': 'approved',
                        'approve_description': message,
                        'is_approve': True,
                        'approve_user_id': self.env.user.id,
                        'approve_date': datetime.now(),
                    })
                    lastApprove = i.sequence == maxSeq
                    break

        if lastApprove:
            self.sudo().write({'state': 'processing'})

        for activity in self.activity_ids:
            activity.sudo().action_feedback(feedback="")

        if not lastApprove:
            self.sudo().send_schedule_actifity()

        return {}
    
    def updateTrxId(self):
        for i in self.approval_info_ids:
            i.write({'trx_id':self.id})

    def cancel_approval(self):
        for i in self.approval_info_ids:
            i.write({
                'is_approve': False,
                'approve_user_id': False,
                'approve_date': False,
            })

    def button_rejected(self):
        # self.cancel_approval()
        okey = self._context.get('okey',False)
        message = self._context.get('message',False)

        if not okey:
            context = {
                'default_message': "",
                'default_data_id':self.id,
                'default_model_name':self._name,
                'default_function_name':"button_rejected",
                # 'default_function_parameter':record.,
            }
            return{
                'type':'ir.actions.act_window',
                'name':'Refuse Reason',
                'res_model':'revise.wizard',
                'view_type':'form',
                'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                'view_mode':'form',
                'target':'new',
                'context':context                
                }
        
        for i in self.approval_info_ids:
            if not i.is_approve:
                i.sudo().write({
                    'state': 'refuse',
                    'approve_description': message,
                    'is_approve': True,
                    'approve_user_id': self.env.user.id,
                    'approve_date': datetime.now(),
                })
                break
        return self.write({"state": "refuse"})
    
    def button_draft(self):
        self.cancel_approval()
        return self.write({"state": "draft"})

    # button dari dess
    def btn_revise(self):
        # self.cancel_approval()
        okey = self._context.get('okey',False)
        message = self._context.get('message',False)

        if not okey:
            context = {
                'default_message': "",
                'default_data_id':self.id,
                'default_model_name':self._name,
                'default_function_name':"btn_revise",
                # 'default_function_parameter':record.,
            }
            return{
                'type':'ir.actions.act_window',
                'name':'Refuse Reason',
                'res_model':'revise.wizard',
                'view_type':'form',
                'view_id': self.env.ref('custom_hr.revise_wizard_form_view').id,
                'view_mode':'form',
                'target':'new',
                'context':context                
                }

        for i in self.approval_info_ids:
            if not i.is_approve:
                i.sudo().write({
                    'state': 'revise',
                    'approve_description': message,
                    'is_approve': True,
                    'approve_user_id': self.env.user.id,
                    'approve_date': datetime.now(),
                })
                break
        return self.write({"state": "revise"})

    def btn_done(self):
        self.employee_id.sudo().write({
            'department_id': self.new_dept_id.id if self.new_dept_id.id else self.old_dept_id.id,
            'section': self.new_section_id.id if self.new_section_id.id else self.old_section_id.id,
            'job_id': self.new_job_id.id if self.new_job_id.id else self.old_job_id.id,
            'resource_calendar_id': self.new_jam_kerja.id if self.new_jam_kerja.id else self.old_jam_kerja.id,
            'employee_type_id': self.new_employee_state.id if self.new_employee_state.id else self.old_employee_state.id,
        })
        return self.write({"state": "done"})
    
    # anwers field
    # Kuantitas Hasil Kerja
    kuantitas_hasil_kerja = fields.Selection(
        string='Kuantitas Hasil Kerja',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    # Kualitas Hasil Kerja
    kualitas_hasil_kerja = fields.Selection(
        string='Kualitas Hasil Kerja',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    # Pengetahuan dan Keterampilan
    pengetahuan_keterampilan = fields.Selection(
        string='Pengetahuan dan Keterampilan',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    # Inisiatif dan Kreatif
    inisiatif_kreatif = fields.Selection(
        string='Inisiatif dan Kreatif',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    # Tanggung Jawab
    tanggung_jawab = fields.Selection(
        string='Tanggung Jawab',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    # Kerjasama
    kerjasama = fields.Selection(
        string='Kerjasama',
        selection=[('1', 'KS'), ('2', 'K'), ('3', 'B'), ('4', 'BS')])
    
    avg_answer = fields.Float(string='Average dari ke-6 Aspek Penilaian', compute="_compute_avg_answer")
    @api.depends('kuantitas_hasil_kerja','kualitas_hasil_kerja',
                 'pengetahuan_keterampilan','inisiatif_kreatif',
                 'tanggung_jawab','kerjasama')
    def _compute_avg_answer(self):
        for rec in self:
            total = 0
            total += int(rec.kuantitas_hasil_kerja) if rec.kuantitas_hasil_kerja else 0
            total += int(rec.kualitas_hasil_kerja) if rec.kualitas_hasil_kerja else 0
            total += int(rec.pengetahuan_keterampilan) if rec.pengetahuan_keterampilan else 0
            total += int(rec.inisiatif_kreatif) if rec.inisiatif_kreatif else 0
            total += int(rec.tanggung_jawab) if rec.tanggung_jawab else 0
            total += int(rec.kerjasama) if rec.kerjasama else 0
            rec.avg_answer = round(total / 6, 2)
    
    sp_type = fields.Selection(
        string='Pilihan SP',
        selection=[('0','None'),('1', 'SP 1'), ('2', 'SP 2'), ('3','SP 3')], default='0')
    pengurang_absensi = fields.Float(string='Pengurang Absensi', compute="_compute_nilai_nilai")
    total_pengurang = fields.Float(string='Total Pengurang', compute="_compute_nilai_nilai")
    total_nilai = fields.Float(string='Total Nilai', compute="_compute_nilai_nilai")
    predikat = fields.Char(string="Predikat", compute="_compute_nilai_nilai")
    @api.depends('avg_answer','sp_type','pengurang_absensi',
                 'sakit','ijin','mangkir','terlambat','pulang_cepat')
    def _compute_nilai_nilai(self):
        def hitungan_sp(sp):
            if sp == '1': return 48.08 / 100
            elif sp == '2': return 64.10 / 100
            elif sp == '3': return 80.13 / 100
            else: return 0
        
        def cari_predikat(predikat):
            if predikat < 2: return 'KS (Kurang Sekali)'
            elif 2 <= predikat <= 2.75: return 'K (Kurang)'
            elif 2.76 <= predikat <= 3.25: return 'B (Baik)'
            elif 3.26 <= predikat <= 4: return 'BS (Baik Sekali)'
            else: return 'Tidak Valid'

        def hitung_pengurang_absen(value):
            ijin = value.ijin * (1.28 / 100)
            sakit = value.sakit * (3.85 / 100)
            mangkir = value.mangkir * (48.08 / 100)
            terlambat = value.terlambat * (2.56 / 100)
            pulang_cepat = value.pulang_cepat * (2.56 / 100)
            res = ijin + sakit + mangkir + terlambat + pulang_cepat
            return round(res, 2)

        for rec in self:
            # hitung nilai sp
            sp = 0.0
            sp = hitungan_sp(rec.sp_type) if rec.sp_type else 0
            sp = round(rec.avg_answer * sp, 2)

            rec.pengurang_absensi = hitung_pengurang_absen(rec)
            rec.total_pengurang = sp + rec.pengurang_absensi
            rec.total_nilai = rec.avg_answer - rec.total_pengurang
            rec.predikat = cari_predikat(rec.total_nilai)
    
    sakit = fields.Float(string="Sakit", default=0)
    ijin = fields.Float(string="Ijin", default=0)
    mangkir = fields.Float(string="Mangkir", default=0)
    terlambat = fields.Float(string="Terlambat", default=0)
    pulang_cepat = fields.Float(string="Pulang Cepat", default=0)

    kelemahan = fields.Text(string='Kelemahan Yang Dimiliki Karyawan')
    kelebihan = fields.Text(string='Kelebihan Yang Dimiliki Karyawan')
    pelatihan = fields.Text(string='Pelatihan Yang Diperlukan')
    catatan_lainnya = fields.Text(string='Catatan Lainnya')
    

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            tmpName = self.env['ir.sequence'].next_by_code('hr.promosi.demosi.mutasi.number') or ('New')
            tmpName = tmpName.replace("(PDM_TYPE)", "/" + str(vals['pdm_type']).upper())
            vals['name'] = tmpName
            
        result = super(hr_promosi_demosi_mutasi, self).create(vals)
        if result:
            if 'approval_info_ids' in vals:
                result.updateTrxId()
        return result

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Tidak dapat menghapus FPSK ini, karna sedang dalam proses Approval.")
            result = super(hr_promosi_demosi_mutasi, rec).unlink()
        return result
    