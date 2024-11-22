from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo import SUPERUSER_ID

from datetime import datetime, date
import secrets


INDEX_NILAI = [
    ('A','A'),
    ('B','B'),
    ('C','C'),
    ('D','D'),
    ('E','E'),
]

class hr_applicant(models.Model):
    _inherit = 'hr.applicant'

    #########################################################
    # access token
    #########################################################
    
    token = fields.Char(string='Token')
    url_form = fields.Char(compute='_compute_url_form', string='URL Form')
    is_second_form_filled = fields.Boolean('Second Form Filled')
    @api.depends('token')
    def _compute_url_form(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.url_form = '{base_url}/jobs/detail-form/{token}'.format(
                base_url = base_url,
                token = record.token
            )

    def generate_unique_token(self):
        unique_token_found = False
        while not unique_token_found:
            token = secrets.token_urlsafe(20)
            if not self.env[self._name].search_count([('token','=',token)]) >= 1:
                unique_token_found = True
        return token

    # action send token
    def action_send_second_form(self):
        for record in self:
            record.token = record.generate_unique_token()


    def write(self, vals):
        res = super(hr_applicant, self).write(vals)
        for record in self:
            if not record.token:
                record.action_send_second_form()
        return res


    user_interviewer_id = fields.Many2one(related="job_id.user_interviewer_id", readonly=False)

    # 1. PERSONAL DATA
    nama_lengkap = fields.Char(related="partner_name",string='Nama Lengkap',readonly=False, tracking=True)
    nama_panggilan = fields.Char(string='Nama Panggilan', tracking=True)
    jenis_kelamin = fields.Selection([
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ], string='Jenis Kelamin', tracking=True)
    tempat_lahir = fields.Char(string='Tempat Lahir', tracking=True)
    tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    umur = fields.Integer(compute='_compute_umur', string='umur')
    
    @api.depends('tanggal_lahir')
    def _compute_umur(self):
        for record in self:
            umur = 0
            if record.tanggal_lahir:
                today = date.today()
                umur = today.year - record.tanggal_lahir.year - ((today.month, today.day) < (record.tanggal_lahir.month, record.tanggal_lahir.day))
            record.umur = umur

    agama = fields.Selection([
        ('islam', 'Islam'),
        ('kristen', 'Kristen'),
        ('Katolik', 'Katolik'),
        ('hindu', 'Hindu'),
        ('buddha', 'Buddha'),
        ('lainnya', 'Lainnya'),
    ], string='Agama', tracking=True)
    no_ktp = fields.Char(string='No KTP', tracking=True)
    kewarganegaraan = fields.Selection([
        ('indonesia', 'Indonesia'),
        ('asing', 'Asing'),
    ], string='Kewarganegaraan', tracking=True)
    alamat_tetap = fields.Char(string='Alamat Tetap', tracking=True)
    kota_tetap = fields.Char(string='Kota', tracking=True)
    kode_pos_tetap = fields.Char(string='Kode POS', tracking=True)
    alamat_sekarang = fields.Char(string='Alamat Sekarang', tracking=True)
    kota_sekarang = fields.Char(string='Kota', tracking=True)
    kode_pos_sekarang = fields.Char(string='Kode POS', tracking=True)
    no_telepon = fields.Char(related="partner_phone",string='No. Telepon',readonly=False, tracking=True)
    no_handphone = fields.Char(related="partner_mobile",string='No. Handphone',readonly=False, tracking=True)
    email = fields.Char(related="email_from",string='Email',readonly=False, tracking=True)
    no_sim_a = fields.Char(string='No. SIM A', tracking=True)
    no_sim_b1 = fields.Char(string='No. SIM B1', tracking=True)
    no_sim_b2 = fields.Char(string='No. SIM B2', tracking=True)
    no_sim_c = fields.Char(string='No. SIM C', tracking=True)
    gol_darah = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('O', 'O'),
        ('AB', 'AB'),
    ], string='Gol. Darah', tracking=True)
    berat_badan = fields.Float(string='Berat Badan (Kg)', tracking=True)
    tinggi_badan = fields.Float(string='Tinggi Badan (Cm)', tracking=True)
    status_pernikahan = fields.Selection([
        ('lajang', 'Lajang'),
        ('menikah', 'Menikah'),
        ('bercerai', 'Bercerai'),
    ], string='Status Pernikahan', tracking=True)


    # 2. Pendidikan
    pendidikan_formal_ids = fields.One2many('hr.applicant.formal_education', 'applicant_id', string='Pendidikan Formal')
    pendidikan_nonformal_ids = fields.One2many('hr.applicant.nonformal_education', 'applicant_id', string='Pendidikan Non Formal')

    # 3. Organisasi
    organization_ids = fields.One2many('hr.applicant.organization', 'applicant_id', string='Organisasi')
    pendidikan_terpuas = fields.Text('Pendidikan Terpuas')
    pendidikan_tertidakpuas = fields.Text('Pendidikan Ter-Tidak puas')
    pendidikan_pembiaya = fields.Text('Pembiaya Pendidikan')


    # 4. Keluarga / Family
    jenis_pasangan = fields.Selection([
        ('istri', 'Istri'),
        ('suami', 'Suami'),
    ], string='Jenis Pasangan', tracking=True)
    pasangan_nama_lengkap = fields.Char(string='Nama Lengkap', tracking=True)
    pasangan_tempat_lahir = fields.Char(string='Tempat Lahir', tracking=True)
    pasangan_tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    pasangan_no_handphone = fields.Char(string='No. handphone', tracking=True)
    pasangan_alamat = fields.Char(string='Alamat', tracking=True)
    pasangan_pendidikan = fields.Char(string='Pendidikan', tracking=True)
    pasangan_pekerjaan = fields.Char(string='Pekerjaan / Perusahaan', tracking=True)

    anak_ids = fields.One2many('hr.applicant.child_data', 'applicant_id', string='Anak')

    # ayah
    ayah_nama_lengkap = fields.Char(string='Nama Lengkap', tracking=True)
    ayah_tempat_lahir = fields.Char(string='Tempat Lahir', tracking=True)
    ayah_tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    ayah_no_handphone = fields.Char(string='No. handphone', tracking=True)
    ayah_alamat = fields.Char(string='Alamat', tracking=True)
    ayah_pendidikan = fields.Char(string='Pendidikan', tracking=True)
    ayah_pekerjaan = fields.Char(string='Pekerjaan / Perusahaan', tracking=True)

    # ibu
    ibu_nama_lengkap = fields.Char(string='Nama Lengkap', tracking=True)
    ibu_tempat_lahir = fields.Char(string='Tempat Lahir', tracking=True)
    ibu_tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    ibu_no_handphone = fields.Char(string='No. handphone', tracking=True)
    ibu_alamat = fields.Char(string='Alamat', tracking=True)
    ibu_pendidikan = fields.Char(string='Pendidikan', tracking=True)
    ibu_pekerjaan = fields.Char(string='Pekerjaan / Perusahaan', tracking=True)

    saudara_ids = fields.One2many('hr.applicant.siblings', 'applicant_id', string='Saudara')

    is_saudara_masih_dibantu = fields.Boolean('Saudara Masih Dibantu?')
    saudara_bantuan_dari = fields.Text('Siapa yang bantu saudara')
    jenis_bentuk_bantuan = fields.Text('Jenis dan Bentuk Bantuan')
    
    is_tanggungan_lain = fields.Boolean('Tanggungan selain istri dan saudara?')
    tanggungan_lain = fields.Text('Tanggungan selain istri dan saudara')

    is_meninggalkan_keluarga = fields.Boolean('pernah meninggalkan keluarga?')
    keperluan_meninggalkan_keluarga = fields.Text('keperluan untuk meninggalkan keluarga')

    rumah_tinggal = fields.Selection([
        ('pribadi', 'Rumah Pribadi'),
        ('keluarga', 'Rumah Keluarga Istri / Suami'),
        ('orang_tua', 'Rumah Orang Tua'),
        ('kontrakan', 'Rumah Kontrakan'),
        ('kost', 'Pondokan / Kost'),
    ], string='Rumah Tinggal')



    # 5. Pengalaman Kerja
    work_experience_ids = fields.One2many('hr.applicant.work_experience', 'applicant_id', string='Work Experience')
    current_position = fields.Char(compute='_compute_current_position', string='current_position')
    current_company = fields.Char(compute='_compute_current_position', string='current_position')
    @api.depends('work_experience_ids')
    def _compute_current_position(self):
        for record in self:
            current_position = ''
            current_company = ''
            if record.work_experience_ids and record.work_experience_ids.filtered(lambda x: x.jabatan):
                current_position = record.work_experience_ids[0].jabatan
                current_company = record.work_experience_ids[0].name
            record.current_position = current_position
            record.current_company = current_company

    jumlah_bawahan = fields.Integer(string='Jumlah Bawahan', tracking=True)
    is_buat_pembaharuan = fields.Boolean(string='Pernah melakukan pembaharuan?', tracking=True)
    pembaharuan_dibuat = fields.Text(string='Pembaharuan apa yg dibuat', tracking=True)

    # 6. Kemampuan Bahasa
    foreign_language_ids = fields.One2many('hr.applicant.foreign_language', 'applicant_id', string='Foreign Language')
    local_language_ids = fields.One2many('hr.applicant.local_language', 'applicant_id', string='Local Language')
    
    # 7. Keterampilan
    skill_ids = fields.One2many('hr.applicant.skills', 'applicant_id', string='Keterampilan')


    # 8. Minat dan konsep diri
    jabatan_dilamar = fields.Many2one(related="job_id", string='Jabatan yg dilamar', tracking=True)
    mengapa_melamar = fields.Text(string='Mengapa melamar jabatan tsb', tracking=True)
    yg_diketahui_dr_jabatan = fields.Text(string='Yg diketahui dr jabatan tsb', tracking=True)
    is_dipindah_jabatan = fields.Boolean(string='ditempatkan di jabatan lain?', tracking=True)
    alasan_pindah_jabatan = fields.Text(string='Alasan Pindah Jabatan', tracking=True)
    lingkungan_disenangi = fields.Selection([
        ('gudang', 'Gudang'),
        ('kantor', 'Kantor'),
        ('lapangan', 'Lapangan'),
        ('laboratorium', 'Laboratorium'),
    ], string='Lingkungan Disenangi', tracking=True)
    alasan_lingkungan_tsb = fields.Text(string='Alasan suka lingungan tsb', tracking=True)
    cita2 = fields.Text(string='cita2 hidup', tracking=True)
    kegemaran = fields.Text(string='hobi dan kegemaran', tracking=True)
    kegiatan_luang = fields.Text(string='bagaimana mengisi waktu luang', tracking=True)
    kelebihan = fields.Text(string='kelebihan', tracking=True)
    kekurangan = fields.Text(string='kekurangan', tracking=True)


    # 9. Riwayat Kesehatan
    pernah_sakit_keras = fields.Boolean(string='Pernah Sakit Keras?', tracking=True)
    sakit_keras_apa = fields.Text(string='Sakit Keras Apa', tracking=True)
    kesehatan_keluarga_baik = fields.Boolean(string='Kesehatan keluarga Baik?', tracking=True)
    keluarga_sakit_apa = fields.Text(string='Keluarga sakit apa', tracking=True)
    pernah_kecelakaan = fields.Boolean(string='Pernah Kecelakaan?', tracking=True)
    kecelakaan_apa = fields.Text(string='Kecelakaan Apa', tracking=True)
    
    
    # 10. Lain lain
    harapan_gaji = fields.Float(string='Harapan Gaji', tracking=True)
    harapan_fasilitas = fields.Text(string='Harapan Fasilitas', tracking=True)
    kesiapan_bekerja = fields.Text(string='Kesiapan bekerja', tracking=True)
    bersedia_diluar_bdg = fields.Boolean('Bersedia diluar bandung?', tracking=True)
    alasan_tidak_diluar_bdg = fields.Boolean('alasan tidak diluar bandung', tracking=True)
    alasan_bekerja_disini = fields.Text(string='Alasan Bekerja Disini', tracking=True)
    sudah_pernah_melamar = fields.Boolean('sudah pernah melamar?', tracking=True)
    kapan_melamar = fields.Text(string='Kapan Melamarnya', tracking=True)
    kendaraan = fields.Text(string='Kendaraan dipunya', tracking=True)
    pernah_psikotest = fields.Boolean('pernah psikotest?', tracking=True)
    terakhir_psikotest = fields.Text(string='Terakhir psikotest', tracking=True)

    # 11. Referensi
    nama_kenalan1 = fields.Char(string='Nama kenalan atau Saudara')
    bagian_kenalan1 = fields.Char(string='Bagian kenalan atau Saudara')

    nama_kenalan2 = fields.Char(string='Nama kenalan atau Saudara 2')
    bagian_kenalan2 = fields.Char(string='Bagian kenalan atau Saudara 2')

    reference_ids = fields.One2many('hr.applicant.reference', 'applicant_id', string='Other Reference')



    # APPRAISALS
    show_interview_form = fields.Boolean(compute='_compute_show_interview_form', string='Show Interview Form')
    
    @api.depends('stage_id')
    def _compute_show_interview_form(self):
        for record in self:
            show_interview_form = True
            stage_list = []
            stage_list.append(self.env.ref('hr_recruitment.stage_job1').id)
            stage_list.append(self.env.ref('custom_hr_recruitment.stage_job_psychotest').id)
            if record.stage_id.id in stage_list:
                show_interview_form = False

            record.show_interview_form = show_interview_form
    
    penilaian_1_education = fields.Selection(INDEX_NILAI,string='Education')
    penilaian_1_job_history = fields.Selection(INDEX_NILAI,string='Job/Work History')
    penilaian_1_motivation = fields.Selection(INDEX_NILAI,string='Motivation')
    penilaian_1_iniciatif = fields.Selection(INDEX_NILAI,string='Iniciatif')
    penilaian_1_discipline = fields.Selection(INDEX_NILAI,string='Discipline')
    penilaian_1_persuasiveness = fields.Selection(INDEX_NILAI,string='Persuasiveness')
    penilaian_1_leadership = fields.Selection(INDEX_NILAI,string='Leadership')
    penilaian_1_human_relation = fields.Selection(INDEX_NILAI,string='Human Relation')
    penilaian_1_verbalization = fields.Selection(INDEX_NILAI,string='Verbalization')
    penilaian_1_appearance = fields.Selection(INDEX_NILAI,string='Appearance')
    penilaian_1_knowledge = fields.Selection(INDEX_NILAI,string='Knowledge')
    penilaian_1_status_penerimaan = fields.Selection([
        ('acceptable', 'Acceptable'),
        ('not_acceptable', 'Not Acceptable'),
    ], string='Status')
    penilaian_1_employee_id = fields.Many2one('hr.employee', string='Approver')
    penilaian_1_date = fields.Datetime('Appraisal Date')

    def action_confirm_penilaian_1(self):
        for record in self:
            if record.penilaian_1_education and record.penilaian_1_job_history and record.penilaian_1_motivation and record.penilaian_1_iniciatif and record.penilaian_1_discipline and record.penilaian_1_persuasiveness and record.penilaian_1_leadership and record.penilaian_1_human_relation and record.penilaian_1_verbalization and record.penilaian_1_appearance and record.penilaian_1_knowledge and record.penilaian_1_status_penerimaan:
                record.penilaian_1_employee_id = self.env.user.employee_id.id if self.env.user.employee_id else None
                record.penilaian_1_date = datetime.now()
            else:
                raise ValidationError("Anda harus mengisi seluruh aspek penilaian terlebih dahulu!")
    
    def action_reset_penilaian_1(self):
        for record in self:
            record.penilaian_1_education = None
            record.penilaian_1_job_history = None
            record.penilaian_1_motivation = None
            record.penilaian_1_iniciatif = None
            record.penilaian_1_discipline = None
            record.penilaian_1_persuasiveness = None
            record.penilaian_1_leadership = None
            record.penilaian_1_human_relation = None
            record.penilaian_1_verbalization = None
            record.penilaian_1_appearance = None
            record.penilaian_1_knowledge = None
            record.penilaian_1_status_penerimaan = None
            record.penilaian_1_employee_id = None
            record.penilaian_1_date = None


    penilaian_2_education = fields.Selection(INDEX_NILAI,string='Education')
    penilaian_2_job_history = fields.Selection(INDEX_NILAI,string='Job/Work History')
    penilaian_2_motivation = fields.Selection(INDEX_NILAI,string='Motivation')
    penilaian_2_iniciatif = fields.Selection(INDEX_NILAI,string='Iniciatif')
    penilaian_2_discipline = fields.Selection(INDEX_NILAI,string='Discipline')
    penilaian_2_persuasiveness = fields.Selection(INDEX_NILAI,string='Persuasiveness')
    penilaian_2_leadership = fields.Selection(INDEX_NILAI,string='Leadership')
    penilaian_2_human_relation = fields.Selection(INDEX_NILAI,string='Human Relation')
    penilaian_2_verbalization = fields.Selection(INDEX_NILAI,string='Verbalization')
    penilaian_2_appearance = fields.Selection(INDEX_NILAI,string='Appearance')
    penilaian_2_knowledge = fields.Selection(INDEX_NILAI,string='Knowledge')
    penilaian_2_status_penerimaan = fields.Selection([
        ('acceptable', 'Acceptable'),
        ('not_acceptable', 'Not Acceptable'),
    ], string='Status')
    penilaian_2_employee_id = fields.Many2one('hr.employee', string='Approver')
    penilaian_2_date = fields.Datetime('Appraisal Date')

    def action_confirm_penilaian_2(self):
        for record in self:
            if record.penilaian_2_education and record.penilaian_2_job_history and record.penilaian_2_motivation and record.penilaian_2_iniciatif and record.penilaian_2_discipline and record.penilaian_2_persuasiveness and record.penilaian_2_leadership and record.penilaian_2_human_relation and record.penilaian_2_verbalization and record.penilaian_2_appearance and record.penilaian_2_knowledge and record.penilaian_2_status_penerimaan:
                record.penilaian_2_employee_id = self.env.user.employee_id.id if self.env.user.employee_id else None
                record.penilaian_2_date = datetime.now()
            else:
                raise ValidationError("Anda harus mengisi seluruh aspek penilaian terlebih dahulu!")
    
    def action_reset_penilaian_2(self):
        for record in self:
            record.penilaian_2_education = None
            record.penilaian_2_job_history = None
            record.penilaian_2_motivation = None
            record.penilaian_2_iniciatif = None
            record.penilaian_2_discipline = None
            record.penilaian_2_persuasiveness = None
            record.penilaian_2_leadership = None
            record.penilaian_2_human_relation = None
            record.penilaian_2_verbalization = None
            record.penilaian_2_appearance = None
            record.penilaian_2_knowledge = None
            record.penilaian_2_status_penerimaan = None
            record.penilaian_2_employee_id = None
            record.penilaian_2_date = None

    
    # @api.constrains('stage_id','write_date')
    # def _constrains_stage_id(self):
    #     for record in self:
    #         hr_interview = self.env.ref('hr_recruitment.stage_job2').id
    #         user_interview = self.env.ref('hr_recruitment.stage_job3').id
    #         if record._origin.stage_id.id == hr_interview and record.stage_id.id == user_interview:
    #             raise UserError("Anda harus mengisi penilaian terlebih dahulu sebelum masuk ke user interview!")


class hr_applicant_formal_education(models.Model):
    _name = 'hr.applicant.formal_education'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Formal Education)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    pendidikan = fields.Selection([
        ('SD', 'SD'),
        ('SMP', 'SMP'),
        ('SMA', 'SMA'),
        ('S1', 'S1'),
        ('S2', 'S2'),
        ('S3', 'S3'),
    ], string='Jenis Pendidikan', required=True, tracking=True)
    nama_sekolah = fields.Char(string='Nama Sekolah', required=True, tracking=True)
    jurusan = fields.Char(string='Jurusan', tracking=True)
    tahun_mulai = fields.Char(string='Tahun Mulai', required=True, tracking=True)    
    tahun_akhir = fields.Char(string='Tahun Akhir', required=True, tracking=True)
    # @api.constrains('tahun_mulai','tahun_akhir')
    # def _constrains_tahun(self):
    #     for record in self:
    #         if record.tahun_mulai and len(str(record.tahun_mulai))>4:
    #             raise ValidationError("Data Tahun Maksimal 4 Digit!")
    #         if record.tahun_akhir and len(str(record.tahun_akhir))>4:
    #             raise ValidationError("Data Tahun Maksimal 4 Digit!")
    ijazah = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada'),
    ], string='Ijazah', required=True, tracking=True)
    ipk = fields.Float(string='IPK', required=True, tracking=True)
    kota = fields.Char(string='Kota', required=True, tracking=True)

class hr_applicant_nonformal_education(models.Model):
    _name = 'hr.applicant.nonformal_education'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Non Formal Education)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    courses = fields.Char(string='Seminar/Kursus/Training', required=True, tracking=True)
    lembaga_pendidikan = fields.Char(string='Lembaga Pendidikan', required=True, tracking=True)
    tahun_mulai = fields.Char(string='Tahun Mulai', tracking=True)    
    tahun_akhir = fields.Char(string='Tahun Akhir', tracking=True)
    # @api.constrains('tahun_mulai','tahun_akhir')
    # def _constrains_tahun(self):
    #     for record in self:
    #         if record.tahun_mulai and len(str(record.tahun_mulai))>4:
    #             raise ValidationError("Data Tahun Maksimal 4 Digit!")
    #         if record.tahun_akhir and len(str(record.tahun_akhir))>4:
    #             raise ValidationError("Data Tahun Maksimal 4 Digit!")
    ijazah = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada'),
    ], string='Ijazah', required=True, tracking=True)
    tingkat = fields.Char(string='Tingkat', tracking=True)
    kota = fields.Char(string='Kota', tracking=True)

class hr_applicant_organization(models.Model):
    _name = 'hr.applicant.organization'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Organization)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    name = fields.Char(string='Nama Organisasi', required=True, tracking=True)
    jenis_kegiatan = fields.Char(string='Jenis Kegiatan', tracking=True)
    position = fields.Char(string='Jabatan', tracking=True)
    tahun = fields.Char(string='Tahun', tracking=True)    
    @api.constrains('tahun')
    def _constrains_tahun(self):
        for record in self:
            if record.tahun and len(str(record.tahun))>4:
                raise ValidationError("Data Tahun Maksimal 4 Digit!")

class hr_applicant_child_data(models.Model):
    _name = 'hr.applicant.child_data'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Children Data)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    name = fields.Char(string='Nama Anak', required=True, tracking=True)
    tempat_lahir = fields.Char(string='Tempat Lahir', tracking=True)
    tanggal_lahir = fields.Date(string='Tanggal Lahir', tracking=True)
    jenis_kelamin = fields.Selection([
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ], string='Jenis Kelamin', tracking=True)
    no_handphone = fields.Char(string='No. handphone', tracking=True)
    pendidikan = fields.Char(string='Pendidikan', tracking=True)
    pekerjaan = fields.Char(string='Pekerjaan / Perusahaan', tracking=True)
    
class hr_applicant_siblings(models.Model):
    _name = 'hr.applicant.siblings'
    _inherit = 'hr.applicant.child_data'
    _description = 'Applicant (Siblings Data)'

class hr_applicant_work_experience(models.Model):
    _name = 'hr.applicant.work_experience'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Work Experience)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    name = fields.Char(string='Nama Perusahaan', required=True, tracking=True)
    mulai = fields.Date(string='Mulai', required=True, tracking=True)
    selesai = fields.Date(string='Selesai', tracking=True)
    alamat = fields.Char(string='Alamat', tracking=True)
    jabatan = fields.Char(string='Jabatan', required=True, tracking=True)
    salary = fields.Float(string='Gaji', tracking=True)
    jobdesk = fields.Text(string='Tugas dan Tanggung Jawab', tracking=True)
    alasan_keluar = fields.Text(string='Alasan keluar', tracking=True)

class hr_applicant_foreign_language(models.Model):
    _name = 'hr.applicant.foreign_language'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Foreign Language)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    name = fields.Char('Jenis Bahasa', required=True, tracking=True)
    tingkat = fields.Selection([
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
    ], string='Tingkat', required=True, tracking=True)

class hr_applicant_local_language(models.Model):
    _name = 'hr.applicant.local_language'
    _inherit = 'hr.applicant.foreign_language'
    _description = 'Applicant (local Language)'

class hr_applicant_skills(models.Model):
    _name = 'hr.applicant.skills'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Skills)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")

    name = fields.Char('Jenis Keterampilan', required=True, tracking=True)
    tingkat = fields.Selection([
        ('baik_sekali', 'Baik Sekali'),
        ('baik', 'Baik'),
        ('cukup', 'Cukup'),
        ('kurang', 'Kurang'),
    ], string='Tingkat', required=True, tracking=True)



    

class hr_applicant_reference(models.Model):
    _name = 'hr.applicant.reference'
    _inherit = ['mail.thread.cc', 'mail.thread', 'mail.activity.mixin']
    _description = 'Applicant (Reference)'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete="cascade")
    

    name = fields.Char(string='Nama', required=True, tracking=True)
    nama_perusahaan = fields.Char(string='Nama Perusahaan', required=True, tracking=True)
    jabatan = fields.Char(string='Jabatan', tracking=True)
    alamat = fields.Char(string='Alamat', tracking=True)