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
class hr_terminasi(models.Model):
    _name = 'hr.terminasi'
    _description = "Pengajuan Terminasi Karyawan"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string="Name", default=lambda self: ('New'), copy=False, index=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    barcode = fields.Char(string="NIK", related='employee_id.barcode')
    identification_id = fields.Char(string="No. KTP", related='employee_id.identification_id')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Department")
    section_id = fields.Many2one('hr.department', related='employee_id.section', string="Section")
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string="Jabatan Lama")

    state = fields.Selection(selection=_STATES, string="Status", index=True,  tracking=True, 
        copy=False, default="draft")
    state_cancel = fields.Selection(related="state", tracking=False)
    state_revise = fields.Selection(related="state", tracking=False)
    state_refuse = fields.Selection(related="state", tracking=False)
    
    # terkait matrik matrik
    matrix_id = fields.Many2one('matrix.approval', string='Matrix Approval', required=True,
        domain=[('model_id.model', '=', 'hr.promosi.demosi.mutasi'),('active','=',True)]) # default=_default_loa
    responsible_id = fields.Many2one('matrix.approval.line', string='Layer / Approval Stage', readonly=True)
    approval_info_ids = fields.Many2many('matrix.approval.info','terminasi_approval_line','terminasi_id','approval_id', 
        string='Approval Information', store=True)
    next_approve_user_ids = fields.Many2many('res.users', 'terminasi_res_user', 'terminasi_id', 'user_id', string='Next Approval', tracking=True, compute="_compute_next_approval")
    is_user_approve_now = fields.Boolean(compute='_get_current_user')
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")

    @api.onchange('department_id')
    def _onchange_for_matrix_id(self):
        for rec in self:
            rec.matrix_id = False
            if rec.department_id and rec.job_id:
                matrix_search = self.env['matrix.approval'].search([
                    ('department_ids','in',[rec.department_id.id]),
                    ('job_ids','in',[rec.job_id.id]),
                    ('model_id.name','=',self._description),
                    ])
                if matrix_search:
                    rec.matrix_id = matrix_search.id
                else:
                    raise ValidationError("Matrix Approval pada Department dan Job Position Berikut Tidak Tersedia, Silahkan Hubungi Service Center!")
                
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
                        "You can't request an approval for a Terminasi "
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
            'active': False,
            # 'department_id': self.department_id.id,
            # 'section_id': self.section_id.id,
            # 'job_id': self.job_id.id,
            # 'resource_calendar_id': self.new_jam_kerja.id,
            # 'employee_type_id': self.new_employee_state.id,
        })
        return self.write({"state": "done"})
        
    def btn_print(self):
        pass
    
    manager_id = fields.Many2one('hr.employee', copy=False, string="Manager", required=True, related='employee_id.parent_id', readonly=False)
    coach_id = fields.Many2one('hr.employee', copy=False, string="Coach", required=True, related='employee_id.coach_id', readonly=False)
    employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type", store=True, tracking=True, related='employee_id.employee_type_id')
    jenis_terminasi_id = fields.Many2one('hr.jenis.terminasi', 
        string="Jenis Terminasi", store=True, tracking=True, required=True)
    need_exit_clearance = fields.Boolean(related='jenis_terminasi_id.need_exit_clearance')
    need_evaluasi = fields.Boolean(related='jenis_terminasi_id.need_evaluasi')
    @api.onchange('employee_type_id')
    def _onchange_employee_type_id(self):
        domain = {'domain': {'jenis_terminasi_id': [('id', 'in', self.employee_type_id.jenis_terminasi_ids.ids)]}}
        self.jenis_terminasi_id = False
        return domain

    join_date = fields.Date(string="Tanggal Masuk", track_visibility='onchange', related='employee_id.join_date')
    resign_pengajuan_date = fields.Date(string="Tanggal Pengajuan Resign", track_visibility='onchange', required=True)
    resign_effective_date = fields.Date(string="Tanggal Effective Resign", track_visibility='onchange', required=True)
    remaining_leaves = fields.Float(string="Sisa Cuti", related="employee_id.remaining_leaves")

    surat_resign = fields.Binary(string='Surat Resign', attachment=True)

    # form exit interview
    # bagian checklist
    checklist_1 = fields.Boolean(string="Memperoleh pekerjaan lain", default=False)
    checklist_2 = fields.Boolean(string="Beban kerja yang terlalu tinggi", default=False)
    checklist_3 = fields.Boolean(string="Memilih untuk berwirausaha", default=False)
    checklist_4 = fields.Boolean(string="Gaji yang kurang seimbang", default=False)
    checklist_5 = fields.Boolean(string="Lokasi kantor terlalu jauh dari rumah", default=False)
    checklist_6 = fields.Boolean(string="Atasan yang kurang mendukung", default=False)
    checklist_7 = fields.Boolean(string="Kondisi kesehatan yang kurang baik", default=False)
    checklist_8 = fields.Boolean(string="Rekan kerja yang kurang menyenangkan", default=False)
    checklist_9 = fields.Boolean(string="Tidak ada kesempatan untuk berkembang", default=False)
    checklist_10 = fields.Boolean(string="Birokrasi yang terlalu rumit", default=False)
    checklist_11 = fields.Boolean(string="Lain-lain", default=False)
    checklist_11_text = fields.Text(string="Lain-lain")

    # bagian radio
    radio_1 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Tugas dan tanggung jawab kerja saya sesuai dengan job deskripsi jabatan tersebut")
    radio_2 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Selama ini saya menyukai rutinitas pekerjaan saya")
    radio_3 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Atasan saya memberikan bimbingan dan pengarahan yang baik selama saya bekerja")
    radio_4 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Saya memperoleh training yang cukup yang menunjang pekerjaan saya")
    radio_5 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Hubungan kerja dengan atasan tidak pernah menyulitkan pekerjaan saya")
    radio_6 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Hubungan kerja dengan rekan kerja tidak pernah menyulitkan pekerjaan saya ")
    radio_7 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Hubungan kerja dengan bawahan tidak pernah menyulitkan pekerjaan saya")
    radio_8 = fields.Selection(selection=[('1','1'),('2','2'),('3','3'),('4','4')], string="Saya menyukai lingkungan kerja perusahaan ini, baik lingkungan fisik kantor maupun lingkungan sosialnya")

    # bagian text
    text_1 = fields.Text(string="Menurut Anda, apa yang perlu diperbaiki di perusahaan ini? Pilihlah sesuai keadaan yang sebenarnya")
    text_2 = fields.Text(string="Menurut Anda apakah daya tarik perusahaan ini ?")
    text_3 = fields.Text(string="dan apakah yang tidak Anda sukai dari perusahaan ini ?")
    text_4 = fields.Text(string="Apakah saran Anda terhadap perusahaan ini untuk perbaikan selanjutnya ?")

    # checklist exit interview
    # dept terkait
    checklist_kertas_kerja = fields.Boolean(string="Kertas Kerja", default=False)
    checklist_document = fields.Boolean(string="Dokumen", default=False)
    checklist_file = fields.Boolean(string="File", default=False)
    checklist_perlengkapan_kerja = fields.Boolean(string="Perlengkapan Kerja", default=False)

    radio_kertas_kerja = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_document = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_file = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_perlengkapan_kerja = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # hrd payroll
    checklist_kasbon = fields.Boolean(string="Kasbon", default=False)
    radio_kasbon = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # hrd medical
    checklist_jamsostek = fields.Boolean(string="Kartu Asuransi Jamsostek", default=False)
    checklist_piut_medical = fields.Boolean(string="Piutang Medical", default=False)

    radio_jamsostek = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_piut_medical = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # hrd ga
    checklist_srt_pengunduran = fields.Boolean(string="Surat Pengunduran Diri", default=False)
    checklist_name_tag = fields.Boolean(string="Name Tag", default=False)
    checklist_kunci_loker = fields.Boolean(string="Kunci Loker", default=False)
    checklist_hp = fields.Boolean(string="Handphone (HP)", default=False)
    checklist_kendaraan = fields.Boolean(string="Kendaraan", default=False)
    checklist_seragam = fields.Boolean(string="Seragam", default=False)
    checklist_sepatu = fields.Boolean(string="Sepatu kerja", default=False)

    radio_srt_pengunduran = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_name_tag = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_kunci_loker = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_hp = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_kendaraan = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_seragam = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_sepatu = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # mis it
    checklist_laptop = fields.Boolean(string="Notebook / Laptop dan Kelengkapannya", default=False)
    radio_laptop = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # finance
    checklist_cash = fields.Boolean(string="Cash Voucher", default=False)
    checklist_bank = fields.Boolean(string="Bank Voucher", default=False)

    radio_cash = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])
    radio_bank = fields.Selection(selection=[('ok','Ok'),('not ok','Not Ok')])

    # Evaluasi karyawan
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
            tmpName = self.env['ir.sequence'].next_by_code('hr.terminasi.number') or ('New')
            vals['name'] = tmpName
            
        result = super(hr_terminasi, self).create(vals)
        if result:
            if 'approval_info_ids' in vals:
                result.updateTrxId()
        return result
    
class hr_jenis_terminasi(models.Model):
    _name = 'hr.jenis.terminasi'
    _description = "Jenis Terminasi"
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string="Name")
    need_exit_clearance = fields.Boolean(default=False)
    need_evaluasi = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
