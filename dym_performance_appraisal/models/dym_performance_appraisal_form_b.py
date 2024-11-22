import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class dym_performance_appraisal_form_b(models.Model):
    _name = 'dym.performance.appraisal.form.b'
    _description = 'Form B Performance Appraisal'

    def _default_department_id(self):
        user_id = self.env.user.id
        if user_id:
            emp = self.env['hr.employee'].search([('user_id','=',user_id)])
            if emp.department_id:
                dep_id = emp.department_id.id
            else:
                dep_id = False
            return dep_id
    
    def _default_periode(self):
        now = datetime.now()
        periode = now.strftime('%Y')

        return periode

    name = fields.Char('Form B Performance Appraisal',readonly=True)
    date = fields.Date('Tanggal',default=fields.Date.context_today)
    department_id = fields.Many2one('hr.department', 'Department', store=True,required=True,default=_default_department_id)
    employee_id = fields.Many2one('hr.employee','Employee',store=True,required=True)
    atasan_1 = fields.Many2one('hr.employee','Atasan 1',store=True,required=True)
    atasan_2 = fields.Many2one('hr.employee','Atasan 2',store=True,required=True)
    job_id = fields.Many2one('hr.job','Job',store=True,required=True)
    loc = fields.Char('Cabang',readonly=True)
    kualitas = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kualitas (Bobot 15)',select="True")
    kuantitas = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kuantitas (Bobot 15)',select="True")
    kerjasama = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kerjasama (Bobot 15)',select="True")
    disiplin = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Disiplin (Bobot 10)',select="True")
    kompetensi = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kompetensi (Bobot 10)',select="True")
    kreatifitas = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kreatifitas (Bobot 10)',select="True")
    konsistensi = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Konsistensi (Bobot 10)',select="True")
    kepemimpinan = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kepemimpinan (Bobot 15)',select="True")
    kualitas_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kualitas (Bobot 15)',select="True")
    kuantitas_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kuantitas (Bobot 15)',select="True")
    kerjasama_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kerjasama (Bobot 15)',select="True")
    disiplin_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Disiplin (Bobot 10)',select="True")
    kompetensi_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kompetensi (Bobot 10)',select="True")
    kreatifitas_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kreatifitas (Bobot 10)',select="True")
    konsistensi_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Konsistensi (Bobot 10)',select="True")
    kepemimpinan_1 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kepemimpinan (Bobot 15)',select="True")
    kualitas_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kualitas (Bobot 15)',select="True")
    kuantitas_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kuantitas (Bobot 15)',select="True")
    kerjasama_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kerjasama (Bobot 15)',select="True")
    disiplin_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Disiplin (Bobot 10)',select="True")
    kompetensi_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kompetensi (Bobot 10)',select="True")
    kreatifitas_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kreatifitas (Bobot 10)',select="True")
    konsistensi_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Konsistensi (Bobot 10)',select="True")
    kepemimpinan_2 = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], string='Kepemimpinan (Bobot 15)',select="True")

    state = fields.Selection([('draft','Draft'),('start','Start'),('employee_answer','Employee Answered'),('atasan1_answer','Atasan 1 Answered'),('atasan2_answer','Atasan 2 Answered'),('posted','Posted'),('cancel','Cancel')],'State',select=True,copy=False,store=True)
    nilai_akhir = fields.Float('Nilai Akhir',readonly=True)
    kekuatan_karyawan = fields.Text('Kekuatan Karyawan')
    kekurangan_karyawan = fields.Text('Kekurangan Karyawan')
    kebutuhan_training = fields.Text('Kebutuhan Training')
    kode_nilai_akhir = fields.Char('Kode Nilai Akhir',readonly=True)
    keterangan_nilai_akhir = fields.Char('Keterangan Nilai Akhir',readonly=True)

    score_kualitas_2 = fields.Float('Score Kualitas',readonly=True)
    score_kuantitas_2 = fields.Float('Score Kuantitas',readonly=True)
    score_kerjasama_2 = fields.Float('Score Kerjasama',readonly=True)
    score_disiplin_2 = fields.Float('Score Disiplin',readonly=True)
    score_kompetensi_2 = fields.Float('Score Kompetensi',readonly=True)
    score_kreatifitas_2 = fields.Float('Score Kreatifitas',readonly=True)
    score_konsistensi_2 = fields.Float('Score Konsistensi',readonly=True)
    score_kepemimpinan_2 = fields.Float('Score Kepemimpinan',readonly=True)
    total_score = fields.Float('Total Score',readonly=True)
    periode = fields.Char('Periode PK',readonly=True,default=_default_periode)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get_sequence_performance(self._cr,self._uid,'FORM-B/PERF')

        now = datetime.now()
        app_id_cek = self.env['dym.performance.appraisal.form.b'].search([('employee_id','=',values['employee_id']),('periode','=',now.strftime('%Y')),('state','!=','cancel')])
        if app_id_cek:
            raise ValidationError('Anda sudah membuat PK pada periode %s, tidak bisa membuat baru lagi!'%(now.strftime('%Y')))

        app_id = super(dym_performance_appraisal_form_b,self).create(values)
        app_id.state = 'draft'
        return app_id
    
    def write(self,values):
        app_id = super(dym_performance_appraisal_form_b,self).write(values)
        return app_id
        
    @api.onchange('department_id')
    def _change_department_id(self):
        dom = {}
        for x in self:
            if x.department_id:
                employee_ids = self.env['hr.employee'].search([('department_id','=',x.department_id.id),('active','=',True)])
                if employee_ids:
                    dom['employee_id'] = [('id','in',employee_ids.ids)]
                x.loc = False
                x.employee_id = False
                x.loc = x.department_id.loc
                
            else:
                x.employee_id = False
                x.loc = False
                x.atasan_1 = False
                x.atasan_2 = False
                x.job_id = False

        return {'domain':dom}
    
    @api.onchange('employee_id')
    def _change_employee_id(self):
        for x in self:
            if x.employee_id:
                # validasi job id
                form_b_job_classification = self.env.ref("dym_performance_appraisal.form_b_job_classification")
                if form_b_job_classification:
                    if x.employee_id.job_id and x.employee_id.job_id.id not in form_b_job_classification.job_ids.ids:
                        raise ValidationError(f'Job Position ini ({x.employee_id.job_id.name}) tidak dapat mengisi form B, silahkan lakukan setting di configuration!')

                if x.employee_id.parent_id:
                    x.atasan_1 = x.employee_id.parent_id.id
                    if x.employee_id.parent_id.parent_id:
                        x.atasan_2 = x.employee_id.parent_id.parent_id.id
                else:
                    x.atasan_1 = False
                    x.atasan_2 = False
                
                x.job_id = x.employee_id.job_id.id
                
            else:
                x.job_id = False
                x.atasan_1 = False
                x.atasan_2 = False

    def start_answer(self):
        if self.employee_id.user_id.id != self._uid:
            raise ValidationError('Hanya Employee yang dapat forward!')
        self.write({
            'state':'start'
        })
    
    # def revise(self):
    #     if self.state == 'employee_answer':
    #         self.write({
    #             'state':'start'
    #         })
    
    def forward_atasan_1(self):
        if self.employee_id.user_id.id != self._uid:
            raise ValidationError('Hanya Employee yang dapat forward!')
        if not self.kualitas:
            raise ValidationError('Kualitas harap diisi!')
        if not self.kuantitas:
            raise ValidationError('Kuantitas harap diisi!')
        if not self.kerjasama:
            raise ValidationError('Kerjasama harap diisi!')
        if not self.disiplin:
            raise ValidationError('Disiplin harap diisi!')
        if not self.kompetensi:
            raise ValidationError('Kompetensi harap diisi!')
        if not self.kreatifitas:
            raise ValidationError('Kreatifitas harap diisi!')
        if not self.konsistensi:
            raise ValidationError('konsistensi harap diisi!')
        if not self.kepemimpinan:
            raise ValidationError('Kepemimpinan harap diisi!')

        self.write({
            'state':'employee_answer'
        })
    def forward_atasan_2(self):
        if self.atasan_1.user_id.id != self._uid:
            raise ValidationError('Hanya Atasan 1 yang dapat forward!')
        if not self.kualitas_1:
            raise ValidationError('Kualitas harap diisi!')
        if not self.kuantitas_1:
            raise ValidationError('Kuantitas harap diisi!')
        if not self.kerjasama_1:
            raise ValidationError('Kerjasama harap diisi!')
        if not self.disiplin_1:
            raise ValidationError('Disiplin harap diisi!')
        if not self.kompetensi_1:
            raise ValidationError('Kompetensi harap diisi!')
        if not self.kreatifitas_1:
            raise ValidationError('Kreatifitas harap diisi!')
        if not self.konsistensi_1:
            raise ValidationError('konsistensi harap diisi!')
        if not self.kepemimpinan_1:
            raise ValidationError('Kepemimpinan harap diisi!')
        self.write({
            'state':'atasan1_answer'
        })
    def atasan2_answer_done(self):
        if self.atasan_2.user_id.id != self._uid:
            raise ValidationError('Hanya Atasan 2 yang dapat forward!')
        if not self.kualitas_2:
            raise ValidationError('Kualitas harap diisi!')
        if not self.kuantitas_2:
            raise ValidationError('Kuantitas harap diisi!')
        if not self.kerjasama_2:
            raise ValidationError('Kerjasama harap diisi!')
        if not self.disiplin_2:
            raise ValidationError('Disiplin harap diisi!')
        if not self.kompetensi_2:
            raise ValidationError('Kompetensi harap diisi!')
        if not self.kreatifitas_2:
            raise ValidationError('Kreatifitas harap diisi!')
        if not self.konsistensi_2:
            raise ValidationError('konsistensi harap diisi!')
        if not self.kepemimpinan_2:
            raise ValidationError('Kepemimpinan harap diisi!')
        self.write({
            'state':'atasan2_answer'
        })
    
    @api.onchange('kualitas','kuantitas','kerjasama','disiplin','kompetensi','kreatifitas','konsistensi','kepemimpinan')
    def onchange_radio_button(self):
        for x in self:
            if x.kualitas or  x.kuantitas or x.kerjasama or x.disiplin or x.kompetensi or x.kreatifitas or x.konsistensi or x.kepemimpinan:
                if x.employee_id.user_id.id != x._uid:
                    raise ValidationError('Hanya Employee yang dapat mengisi!')

    @api.onchange('kualitas_1','kuantitas_1','kerjasama_1','disiplin_1','kompetensi_1','kreatifitas_1','konsistensi_1','kepemimpinan_1')
    def onchange_radio_button_1(self):
        for x in self:
            if x.kualitas_1 or  x.kuantitas_1 or x.kerjasama_1 or x.disiplin_1 or x.kompetensi_1 or x.kreatifitas_1 or x.konsistensi_1 or x.kepemimpinan_1:
                if x.atasan_1.user_id.id != x._uid:
                    raise ValidationError('Hanya Atasan 1 yang dapat mengisi!')
    
    @api.onchange('kualitas_2','kuantitas_2','kerjasama_2','disiplin_2','kompetensi_2','kreatifitas_2','konsistensi_2','kepemimpinan_2')
    def onchange_radio_button_2(self):
        for x in self:
            if x.kualitas_2 or  x.kuantitas_2 or x.kerjasama_2 or x.disiplin_2 or x.kompetensi_2 or x.kreatifitas_2 or x.konsistensi_2 or x.kepemimpinan_2:
                if x.atasan_2.user_id.id != x._uid:
                    raise ValidationError('Hanya Atasan 2 yang dapat mengisi!')
    
    def calculate_nilai(self):
        #FORM B
        if self.atasan_2.user_id.id != self._uid:
            raise ValidationError('Hanya Atasan 2 yang dapat mengcalculate nilai akhir!')
        kualitas = 15 * int(self.kualitas_2)
        kuantitas = 15 * int(self.kuantitas_2)
        kerjasama = 15 * int(self.kerjasama_2)
        disiplin = 10 * int(self.disiplin_2)
        kompetensi = 10 * int(self.kompetensi_2)
        kreatifitas = 10 * int(self.kreatifitas_2)
        konsistensi = 10 * int(self.konsistensi_2)
        kepemimpinan = 15 * int(self.kepemimpinan_2)

        nilai_akhir = (kualitas + kuantitas + kerjasama + disiplin + kompetensi + kreatifitas + konsistensi + kepemimpinan) / 100
        if nilai_akhir <= 2:
            kode = 'KURANG'
        elif nilai_akhir <= 2.75 and nilai_akhir > 2:
            kode = 'CUKUP'
        elif nilai_akhir <= 3 and nilai_akhir > 2.75:
            kode = 'B-'
        elif nilai_akhir <= 3.25 and nilai_akhir > 3:
            kode = 'BAIK'
        elif nilai_akhir <= 3.5 and nilai_akhir > 3.25:
            kode = 'B+'
        elif nilai_akhir <= 4.5 and nilai_akhir > 3.5:
            kode = 'BAIK SEKALI'
        elif nilai_akhir <= 5 and nilai_akhir > 4.5:
            kode = 'ISTIMEWA'

        self.nilai_akhir = nilai_akhir
        self.kode_nilai_akhir = kode
        self.keterangan_nilai_akhir = kode + ' (' + str(nilai_akhir) + ')'

        self.score_kualitas_2 = kualitas
        self.score_kuantitas_2 = kuantitas
        self.score_kerjasama_2 = kerjasama
        self.score_disiplin_2 = disiplin
        self.score_kompetensi_2 = kompetensi
        self.score_kreatifitas_2 = kreatifitas
        self.score_konsistensi_2 = konsistensi
        self.score_kepemimpinan_2 = kepemimpinan
        self.total_score = (kualitas + kuantitas + kerjasama + disiplin + kompetensi + kreatifitas + konsistensi + kepemimpinan)
        self.write({
            'state':'posted'
        })
    
    def cancel(self):
        if self.atasan_2.user_id.id != self._uid:
            raise ValidationError('Hanya Atasan 2 yang dapat mengcancel')
        self.write({
            'state':'cancel'
        })
    
    # def set_to_draft(self):
    #     self.write({
    #         'state':'draft'
    #     })

    def revise(self):
        if self.atasan_2.user_id.id != self._uid:
            raise ValidationError('Hanya Atasan 2 yang dapat mengcancel')

        cek_entry = self.env['dym.performance.appraisal.form.b'].search([('employee_id','=',self.employee_id.id),('state','!=','cancel'),('id','!=',self.id)])
        if cek_entry:
            raise ValidationError('Sudah ada entry baru dengan karyawan yang dinilai dengan nomor %s, tidak bisa revise!'%(cek_entry.name))
        
        self.state = 'atasan1_answer'
        self.nilai_akhir = False
        self.kekuatan_karyawan = False
        self.kekurangan_karyawan = False
        self.kebutuhan_training = False
        self.kode_nilai_akhir = False
        self.keterangan_nilai_akhir = False

        self.kualitas_2 = False
        self.kuantitas_2 = False
        self.kerjasama_2 = False
        self.disiplin_2 = False
        self.kompetensi_2 = False
        self.kreatifitas_2 = False
        self.konsistensi_2 = False
        self.kepemimpinan_2 = False

        self.score_kualitas_2 = False
        self.score_kuantitas_2 = False
        self.score_kerjasama_2 = False
        self.score_disiplin_2 = False
        self.score_kompetensi_2 = False
        self.score_kreatifitas_2 = False
        self.score_konsistensi_2 = False
        self.score_kepemimpinan_2 = False
        self.total_score = False


class dym_sequence(models.Model):
    _inherit = 'ir.sequence'

    def get_sequence_performance(self, cr, uid, first_prefix, padding=5, context=None):
            ids = self.search([('name','=',first_prefix),('padding','=',padding)])
            if not ids:
                prefix = first_prefix + '/%(y)s%(month)s/'
                ids = self.create({'name': first_prefix,
                                    'implementation': 'no_gap',
                                    'prefix': prefix,
                                    'padding': padding})
                
            return self.get_id(ids.id)
                    
                
                